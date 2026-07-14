"""Deterministic, Feishu-safe SVG whiteboard rendering."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import re
from typing import Any, Dict, Iterable, List, Tuple
from xml.etree import ElementTree

from .model import BodyValidationError


CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 900
ALLOWED_ELEMENTS = frozenset(
    {"svg", "g", "rect", "circle", "ellipse", "line", "polyline", "text", "tspan"}
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


def render_workflow_svg(section: Dict[str, Any]) -> str:
    """Render up to six workflow steps as an editable 16:9 board."""

    steps = list(section.get("steps") or [])
    if not steps:
        raise ValueError("whiteboard_workflow requires at least one step")
    if len(steps) > 6:
        raise ValueError("whiteboard_workflow supports at most six steps in v0.1")

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

    title = escape(str(section.get("title", "业务交付链路")))
    return "".join(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" '
            'viewBox="0 0 1600 900">',
            '<rect x="0" y="0" width="1600" height="900" fill="#EFE7D4"/>',
            '<rect x="80" y="70" width="330" height="44" fill="#E89CB1" '
            'stroke="#2E4A2A" stroke-width="2"/>',
            '<text x="245" y="99" text-anchor="middle" font-size="18" font-weight="700" '
            'fill="#243A21">STANDARD WORKFLOW</text>',
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
            '同一份 Body，稳定生成正文、画板、清单与交付证据。</text>',
            '<text x="1500" y="845" text-anchor="end" font-size="20" font-weight="700" '
            'fill="#2E4A2A">HEIGE FEISHU WORD · MVP</text>',
            "</svg>",
        )
    )


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
    if root.attrib.get("height") != str(CANVAS_HEIGHT):
        errors.append("canvas height must be 900")
    if root.attrib.get("viewBox") != "0 0 1600 900":
        errors.append("viewBox must be 0 0 1600 900")

    text_nodes = 0
    for element in root.iter():
        element_name = _local_name(element.tag)
        if element_name not in ALLOWED_ELEMENTS:
            errors.append(f"unsupported SVG element: {element_name}")
        if element_name == "text":
            text_nodes += 1
        for attribute in element.attrib:
            if attribute in FORBIDDEN_ATTRIBUTES or attribute.startswith("on"):
                errors.append(f"unsupported SVG attribute: {attribute}")

    if text_nodes < 2:
        warnings.append("board contains very few editable text nodes")
    return SvgValidationReport(tuple(dict.fromkeys(errors)), tuple(warnings))
