"""Render a validated Document Body into Feishu Docx XML."""

from __future__ import annotations

from html import escape
from typing import Any, Callable, Dict, Iterable, List

from .model import validate_body
from .svg_renderer import render_workflow_svg


def _e(value: Any) -> str:
    return escape(str(value), quote=False).replace("\n", "<br/>")


def _section_title(section: Dict[str, Any]) -> str:
    title = section.get("title")
    return f"<h2>{_e(title)}</h2>" if title else ""


def _balanced_ratios(count: int) -> List[str]:
    if count <= 1:
        return ["1"]
    if count == 2:
        return ["0.5", "0.5"]
    if count == 3:
        return ["0.34", "0.33", "0.33"]
    return ["0.25"] * min(count, 4)


def _chunks(items: List[Dict[str, Any]], size: int = 3) -> Iterable[List[Dict[str, Any]]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def _render_callout(section: Dict[str, Any]) -> str:
    tone = str(section.get("tone", "info"))
    palette = {
        "success": ("✅", "light-green", "green", "green"),
        "warning": ("❗", "light-yellow", "yellow", "orange"),
        "risk": ("⚠️", "light-red", "red", "red"),
        "info": ("ℹ️", "light-blue", "blue", "blue"),
    }
    emoji, background, border, text = palette.get(tone, palette["info"])
    body = _e(section.get("body", ""))
    return "".join(
        (
            _section_title(section),
            f'<callout emoji="{emoji}" background-color="{background}" '
            f'border-color="{border}" text-color="{text}">',
            f"<p><b>{body}</b></p>",
            "</callout>",
        )
    )


def _render_metrics(section: Dict[str, Any]) -> str:
    items = list(section.get("items") or [])
    grids = []
    for row in _chunks(items):
        ratios = _balanced_ratios(len(row))
        columns = []
        for index, item in enumerate(row):
            value = _e(item.get("value", ""))
            label = _e(item.get("label", ""))
            note = _e(item.get("note", ""))
            columns.append(
                f'<column width-ratio="{ratios[index]}">'
                f'<h3><span text-color="green">{value}</span></h3>'
                f"<p><b>{label}</b></p>"
                f'<p><span text-color="gray">{note}</span></p>'
                "</column>"
            )
        grids.append("<grid>" + "".join(columns) + "</grid>")
    return _section_title(section) + "".join(grids)


def _render_table(section: Dict[str, Any]) -> str:
    columns = list(section.get("columns") or [])
    rows = list(section.get("rows") or [])
    header = "".join(
        f'<th background-color="light-gray"><b>{_e(column)}</b></th>'
        for column in columns
    )
    body_rows = []
    for row in rows:
        cells = "".join(f'<td vertical-align="top">{_e(cell)}</td>' for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return "".join(
        (
            _section_title(section),
            "<table>",
            f"<thead><tr>{header}</tr></thead>",
            f"<tbody>{''.join(body_rows)}</tbody>",
            "</table>",
        )
    )


def _render_grid(section: Dict[str, Any]) -> str:
    items = list(section.get("items") or [])
    grids = []
    for row in _chunks(items):
        ratios = _balanced_ratios(len(row))
        columns = []
        for index, item in enumerate(row):
            columns.append(
                f'<column width-ratio="{ratios[index]}">'
                f"<h3>{_e(item.get('title', ''))}</h3>"
                f"<p>{_e(item.get('body', ''))}</p>"
                "</column>"
            )
        grids.append("<grid>" + "".join(columns) + "</grid>")
    return _section_title(section) + "".join(grids)


def _render_workflow(section: Dict[str, Any]) -> str:
    svg = render_workflow_svg(section)
    return "".join(
        (
            _section_title(section),
            f'<whiteboard type="svg">{svg}</whiteboard>',
            '<p><span text-color="gray">该流程图由原生节点组成，可在飞书画板中继续编辑。</span></p>',
        )
    )


def _render_actions(section: Dict[str, Any]) -> str:
    checkboxes = []
    for item in section.get("items") or []:
        owner = _e(item.get("owner", "待认领"))
        action = _e(item.get("action", ""))
        due = _e(item.get("due", "待确认"))
        checkboxes.append(
            f'<checkbox done="false"><b>{owner}</b>｜{action}｜'
            f'<span background-color="light-blue">{due}</span></checkbox>'
        )
    return _section_title(section) + "".join(checkboxes)


SECTION_RENDERERS: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "callout": _render_callout,
    "metrics": _render_metrics,
    "table": _render_table,
    "grid": _render_grid,
    "whiteboard_workflow": _render_workflow,
    "actions": _render_actions,
}


def _meta_line(meta: Dict[str, Any]) -> str:
    parts: Iterable[str] = (
        str(meta.get("status", "")).strip(),
        str(meta.get("reading_time", "")).strip(),
    )
    visible = [part for part in parts if part]
    return " · ".join(visible)


def render_document_xml(body: Dict[str, Any]) -> str:
    """Render a complete Feishu XML fragment from a validated Body."""

    validate_body(body)
    meta = body["meta"]
    title = _e(meta["title"])
    blocks = [f"<title>{title}</title>", f"<h1>{title}</h1>"]

    subtitle = str(meta.get("subtitle", "")).strip()
    if subtitle:
        blocks.append(f"<p><b>{_e(subtitle)}</b></p>")

    meta_line = _meta_line(meta)
    if meta_line:
        blocks.append(
            f'<p><span background-color="light-green">{_e(meta_line)}</span></p>'
        )

    audience = meta.get("audience") or []
    if audience:
        blocks.append(
            f'<p><span text-color="gray">适用读者：{_e("、".join(audience))}</span></p>'
        )
    blocks.append("<hr/>")

    for section in body["sections"]:
        blocks.append(SECTION_RENDERERS[section["type"]](section))
        blocks.append("<hr/>")

    blocks.append(
        '<callout emoji="📌" background-color="light-gray" border-color="gray">'
        '<p>标准样本只用于验证内容结构、视觉层级和交付链路。所有数字均为试点目标。</p>'
        "</callout>"
    )
    return "\n".join(blocks) + "\n"
