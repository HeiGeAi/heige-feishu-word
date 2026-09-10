"""Deterministic, Feishu-safe SVG whiteboard rendering."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Tuple
from xml.etree import ElementTree

from .model import BodyValidationError


CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 900
ALLOWED_ELEMENTS = frozenset(
    {"svg", "g", "rect", "circle", "ellipse", "line", "polyline", "polygon", "path", "text", "tspan"}
)
FORBIDDEN_ATTRIBUTES = frozenset(
    {"filter", "mask", "clip-path", "opacity", "fill-opacity", "stroke-opacity", "href"}
)


@dataclass(frozen=True)
class SvgValidationReport:
    """Static validation result for a generated board."""

    errors: Tuple[str, ...]
    warnings: Tuple[str, ...]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _wrap_text(text: str, line_length: int = 18) -> List[str]:
    """Wrap mixed Chinese and Latin copy without relying on browser layout."""

    compact = " ".join(str(text).split())
    if not compact:
        return [""]
    tokens = re.findall(r"[A-Za-z0-9]+|[^A-Za-z0-9]", compact)
    lines: List[str] = []
    current = ""
    for token in tokens:
        if len(current) + len(token) <= line_length:
            current += token
            continue
        if current.strip():
            lines.append(current.rstrip())
            current = ""
        while len(token) > line_length:
            lines.append(token[:line_length])
            token = token[line_length:]
        current = token.lstrip()
    if current.strip():
        lines.append(current.rstrip())
    if len(lines)>1 and len(lines[-1])<=3:
        tail=lines[-2]+lines[-1]
        breaks=[i+1 for i,c in enumerate(tail) if c in '，；。' and 4<=i+1<=line_length and 4<=len(tail)-i-1<=line_length]
        if breaks:
            split=min(breaks,key=lambda i:abs(i*2-len(tail)))
            lines[-2:]=[tail[:split],tail[split:]]
        else:
            while len(lines[-1])<4 and len(lines[-2])>1 and ord(lines[-2][-1])>255:
                lines[-1]=lines[-2][-1]+lines[-1]
                lines[-2]=lines[-2][:-1]
    return lines or [""]


def _text_lines(
    lines: Iterable[str],
    *,
    x: int,
    y: int,
    font_size: int,
    fill: str,
    line_height: int,
    font_weight: int = 400,
) -> str:
    escaped_lines = [escape(line) for line in lines]
    tspans = []
    for index, line in enumerate(escaped_lines):
        dy = 0 if index == 0 else line_height
        tspans.append(f'<tspan x="{x}" dy="{dy}">{line}</tspan>')
    return (
        f'<text x="{x}" y="{y}" font-size="{font_size}" '
        f'font-weight="{font_weight}" fill="{fill}">'
        + "".join(tspans)
        + "</text>"
    )


def _card_svg(step: Dict[str, Any], number: int, x: int, y: int, fill: str) -> str:
    title = escape(str(step.get("title", "")))
    description = _wrap_text(str(step.get("description", "")), 17)
    if len(description) > 3:
        raise BodyValidationError(
            f"workflow step description is too long to fit card {number}"
        )
    number_text = f"{number:02d}"
    return "".join(
        (
            f'<rect x="{x}" y="{y}" width="430" height="210" fill="{fill}" '
            'stroke="#2E4A2A" stroke-width="3"/>',
            f'<rect x="{x + 24}" y="{y + 24}" width="72" height="58" fill="#E89CB1" '
            'stroke="#2E4A2A" stroke-width="2"/>',
            f'<text x="{x + 60}" y="{y + 63}" text-anchor="middle" font-size="25" '
            f'font-weight="700" fill="#243A21">{number_text}</text>',
            f'<text x="{x + 118}" y="{y + 62}" font-size="27" font-weight="700" '
            f'fill="#2E4A2A">{title}</text>',
            f'<line x1="{x + 24}" y1="{y + 100}" x2="{x + 406}" y2="{y + 100}" '
            'stroke="#2E4A2A" stroke-width="2"/>',
            _text_lines(
                description,
                x=x + 24,
                y=y + 137,
                font_size=21,
                fill="#1A1A17",
                line_height=29,
            ),
        )
    )


def _flow_em(text: str) -> float:
    return sum(0.0 if unicodedata.combining(c) else (1.0 if unicodedata.east_asian_width(c) in "WF" else 0.6) for c in text)


def _flow_lines(text: str, width: float, path: str, limit: int) -> List[str]:
    """Wrap complete copy by its estimated rendered width, preserving all glyphs."""
    if not isinstance(text, str) or not text.strip():
        raise BodyValidationError(f"{path} must be a non-empty string")
    lines: List[str] = []
    for paragraph in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        wrapped: List[str] = []
        current = ""
        for token in re.findall(r"[A-Za-z0-9_]+|[^A-Za-z0-9_]", paragraph):
            if _flow_em(token) > width:
                raise BodyValidationError(f"{path} contains a word too long to fit the embedded workflow; no text was truncated")
            if current and _flow_em(current + token) > width:
                wrapped.append(current)
                current = ""
            current += token
        if current or not wrapped:
            wrapped.append(current)
        if len(wrapped) > 1 and _flow_em(wrapped[-1]) <= 3:
            tail = wrapped[-2] + wrapped[-1]
            breaks = [i + 1 for i, c in enumerate(tail) if c in "，；。" and 4 <= _flow_em(tail[:i+1]) <= width and 4 <= _flow_em(tail[i+1:]) <= width]
            if breaks:
                split = min(breaks, key=lambda i: abs(_flow_em(tail[:i]) - _flow_em(tail[i:])))
                wrapped[-2:] = [tail[:split], tail[split:]]
            else:
                while _flow_em(wrapped[-1]) < 4 and len(wrapped[-2]) > 1 and unicodedata.east_asian_width(wrapped[-2][-1]) in "WF":
                    wrapped[-1] = wrapped[-2][-1] + wrapped[-1]
                    wrapped[-2] = wrapped[-2][:-1]
        lines.extend(wrapped)
    if len(lines) > limit:
        raise BodyValidationError(f"{path} is too long: requires {len(lines)} lines, exceeding {limit} readable lines in the embedded workflow; shorten the copy or split the workflow. No text was truncated.")
    return lines


def _embedded_workflow_svg(steps: List[Dict[str, Any]], theme) -> str:
    from .themes import get_theme
    from .charts import _theme as chart_theme

    visual = theme if theme is not None else get_theme()
    for key in ("surface", "ink", "hairline", "primary"):
        if not isinstance(visual.get(key), str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", visual[key]):
            raise BodyValidationError(f"theme.{key} must be a six-digit hexadecimal color")
    try:
        visual = chart_theme(visual)
    except ValueError as exc:
        raise BodyValidationError(str(exc)) from exc
    ink, primary, hairline = visual["ink"], visual["primary"], visual["hairline"]
    columns = len(steps) if len(steps) <= 4 else 3
    gap, margin = 40, 48
    width = (CANVAS_WIDTH - margin * 2 - gap * (columns - 1)) / columns
    prepared = []
    for index, step in enumerate(steps):
        path = f"workflow.steps[{index}]"
        title = _flow_lines(step.get("title"), (width - 58) / 32, path + ".title", 2)
        description = _flow_lines(step.get("description"), width / 28, path + ".description", 5)
        prepared.append((title, description))
    row_specs = []
    top = 24
    for start in range(0, len(steps), columns):
        row = prepared[start:start + columns]
        title_lines = max(len(item[0]) for item in row)
        body_lines = max(len(item[1]) for item in row)
        row_height = title_lines * 40 + body_lines * 36 + 40
        row_specs.append((start, top, title_lines, row_height))
        top += row_height + 64
    height = max(240, top - 64 + 24)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}" font-family="Noto Sans SC, sans-serif">',
             f'<rect x="0" y="0" width="1600" height="{height}" fill="#FFFFFF"/>']
    for row_index, (start, top, title_lines, row_height) in enumerate(row_specs):
        count = min(columns, len(steps) - start)
        for column in range(count):
            index = start + column
            x = margin + column * (width + gap)
            title, description = prepared[index]
            color = visual["palette"][index % len(visual["palette"])]
            tint = visual["tints"][index % len(visual["tints"])]
            parts += [f'<g id="workflow-step-{index+1}">',
                      f'<rect x="{x-8:g}" y="{top-12:g}" width="{width+16:g}" height="{row_height+16:g}" fill="{tint}"/>',
                      f'<rect x="{x+58:g}" y="{top-2:g}" width="64" height="3" fill="{color}"/>',
                      f'<circle cx="{x+20:g}" cy="{top+24:g}" r="20" fill="#FFFFFF" stroke="{color}" stroke-width="2"/>',
                      f'<text x="{x+20:g}" y="{top+33:g}" text-anchor="middle" font-size="26" font-weight="600" fill="{color}">{index+1}</text>',
                      _text_lines(title, x=x+58, y=top+34, font_size=32, fill=ink, line_height=40, font_weight=600),
                      _text_lines(description, x=x, y=top+title_lines*40+48, font_size=28, fill=ink, line_height=36),
                      '</g>']
            if column + 1 < count:
                left, right, y = x + width + 10, x + width + gap - 12, top + 24
                parts += [f'<line x1="{left:g}" y1="{y:g}" x2="{right:g}" y2="{y:g}" stroke="{color}" stroke-width="2"/>',
                          f'<polyline points="{right-6:g},{y-6:g} {right:g},{y:g} {right-6:g},{y+6:g}" fill="none" stroke="{color}" stroke-width="2"/>']
        if row_index + 1 < len(row_specs):
            next_top = row_specs[row_index+1][1]
            middle_y = top + row_height + 32
            points = f"1562,{top+24:g} 1576,{top+24:g} 1576,{middle_y:g} 24,{middle_y:g} 24,{next_top+24:g} 36,{next_top+24:g}"
            parts += [f'<polyline points="{points}" fill="none" stroke="{hairline}" stroke-width="2"/>',
                      f'<polyline points="30,{next_top+18:g} 36,{next_top+24:g} 30,{next_top+30:g}" fill="none" stroke="{primary}" stroke-width="2"/>']
    return "".join(parts) + "</svg>"


def render_workflow_svg(section: Dict[str, Any], theme=None, *, embedded: bool = False) -> str:
    """Render up to six steps as a standalone board or a compact document figure."""

    steps = list(section.get("steps") or [])
    if not steps:
        raise ValueError("whiteboard_workflow requires at least one step")
    if len(steps) > 6:
        raise ValueError("whiteboard_workflow supports at most six steps in v0.1")
    if embedded:
        return _embedded_workflow_svg(steps, theme)

    positions = (
        (80, 250),
        (570, 250),
        (1060, 250),
        (1060, 525),
        (570, 525),
        (80, 525),
    )
    fills = ("#FFFFFF", "#E5EDD6", "#F2D4CF", "#FFFFFF", "#E5EDD6", "#F2D4CF")
    cards = [
        _card_svg(step, index + 1, *positions[index], fills[index])
        for index, step in enumerate(steps)
    ]

    connector_specs = (
        (518, 355, 562, 355),
        (1008, 355, 1052, 355),
        (1275, 468, 1275, 517),
        (1008, 630, 1052, 630),
        (518, 630, 562, 630),
    )
    connectors = [
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        'stroke="#2E4A2A" stroke-width="5"/>'
        for x1, y1, x2, y2 in connector_specs[: max(0, len(steps) - 1)]
    ]

    raw_title = str(section.get("title", "业务交付链路"))
    if len(raw_title) > 18:
        raise BodyValidationError("workflow title too long to fit; use at most 18 characters")
    for step in steps:
        if sum(1 if ord(c) > 255 else 0.6 for c in step["title"]) > 10.65:
            raise BodyValidationError("workflow step title too long to fit; use at most 11 characters")
    title = escape(raw_title)
    rendered = "".join(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" '
            'viewBox="0 0 1600 900">',
            '<rect x="0" y="0" width="1600" height="900" fill="#EFE7D4"/>',
            '<rect x="80" y="70" width="330" height="44" fill="#E89CB1" '
            'stroke="#2E4A2A" stroke-width="2"/>',
            '<text x="245" y="99" text-anchor="middle" font-size="18" font-weight="700" '
            'fill="#243A21">WORKFLOW</text>',
            f'<text x="80" y="183" font-size="54" font-weight="700" fill="#2E4A2A">{title}</text>',
            '<rect x="1130" y="96" width="370" height="64" fill="#E6DCC4" '
            'stroke="#2E4A2A" stroke-width="2"/>',
            '<text x="1315" y="136" text-anchor="middle" font-size="22" '
            'font-weight="700" fill="#2E4A2A">可编辑 · 可追溯 · 可验证</text>',
            '<line x1="80" y1="214" x2="1500" y2="214" stroke="#2E4A2A" stroke-width="3"/>',
            *cards,
            *connectors,
            '<line x1="80" y1="798" x2="1500" y2="798" stroke="#2E4A2A" stroke-width="2"/>',
            '<text x="80" y="845" font-size="20" fill="#1A1A17">'
            '按编号阅读流程，详细说明见正文。</text>',
            '<text x="1500" y="845" text-anchor="end" font-size="20" font-weight="700" '
            'fill="#2E4A2A">HEIGE FEISHU WORD</text>',
            "</svg>",
        )
    )
    if theme:
        replacements = {"#EFE7D4": theme["canvas"], "#FFFFFF": theme["surface"],
                        "#2E4A2A": theme["ink"], "#1A1A17": theme["ink"],
                        "#E89CB1": theme["hairline"], "#243A21": theme["ink"],
                        "#E5EDD6": theme["surface"], "#F2D4CF": theme["surface"],
                        "#E6DCC4": theme["surface"]}
        # Match only generated paint attributes, never user-authored text.
        rendered = re.sub(
            r'(\b(?:fill|stroke)=")(' + "|".join(replacements) + r')(")',
            lambda m: m.group(1) + replacements[m.group(2)] + m.group(3),
            rendered,
        )
    return rendered



def validate_svg(svg: str) -> SvgValidationReport:
    """Validate XML structure and the supported Feishu SVG subset."""

    errors: List[str] = []
    warnings: List[str] = []
    try:
        root = ElementTree.fromstring(svg)
    except ElementTree.ParseError as exc:
        return SvgValidationReport((f"invalid SVG XML: {exc}",), ())

    if _local_name(root.tag) != "svg":
        errors.append("root element must be svg")
    if root.attrib.get("width") != str(CANVAS_WIDTH):
        errors.append("canvas width must be 1600")
    height = root.attrib.get("height", "")
    if not re.fullmatch(r"[0-9]+", height) or not 240 <= int(height) <= 1000:
        errors.append("canvas height must be an integer from 240 to 1000")
    elif root.attrib.get("viewBox") != f"0 0 1600 {int(height)}":
        errors.append(f"viewBox must be 0 0 1600 {int(height)}")

    text_nodes = 0
    for element in root.iter():
        element_name = _local_name(element.tag)
        if element_name not in ALLOWED_ELEMENTS:
            errors.append(f"unsupported SVG element: {element_name}")
        if element_name == "text":
            text_nodes += 1
        for attribute in element.attrib:
            if _local_name(attribute) in FORBIDDEN_ATTRIBUTES or _local_name(attribute).lower().startswith("on") or "url(" in element.attrib[attribute].lower():
                errors.append(f"unsupported SVG attribute: {attribute}")

    if text_nodes < 2:
        warnings.append("board contains very few editable text nodes")
    return SvgValidationReport(tuple(dict.fromkeys(errors)), tuple(warnings))
