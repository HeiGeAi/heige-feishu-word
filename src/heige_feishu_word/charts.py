"""Deterministic data charts in the self-contained Feishu whiteboard SVG subset.

Data is never abbreviated, reordered or silently discarded.  The fixed canvas
has an explicit text budget; a chart that cannot remain legible raises an error.
"""

from __future__ import annotations

from decimal import Decimal, localcontext, ROUND_FLOOR
from html import escape
import math
import re
import unicodedata
from typing import Any, Dict, List, Tuple


_FIELDS = frozenset({"id", "type", "title", "kind", "labels", "series", "unit", "source", "insight"})
_KINDS = {"bar": "横向对比", "line": "趋势变化", "donut": "构成占比", "funnel": "阶段转化", "progress": "目标进度"}
_SERIES_LIMIT = {"bar": 2, "line": 3, "donut": 1, "funnel": 1, "progress": 1}
_COLORS = ("canvas", "surface", "ink", "muted", "hairline", "primary", "secondary")
_DEFAULT_THEME = {
    "canvas": "#F4F0E8", "surface": "#FFFFFF", "ink": "#18332E",
    "muted": "#53665F", "hairline": "#C9D3CC", "primary": "#285A48",
    "secondary": "#C75A39", "palette": ["#285A48", "#C75A39", "#47748C", "#A67B35", "#77518A", "#318383", "#A24765", "#687533"],
    "slug": "editorial", "layout": "editorial",
}


def _em(text: str) -> float:
    """Conservative Noto Sans SC width in em, including wide emoji characters."""
    return sum(0.0 if unicodedata.combining(char) else (1.0 if unicodedata.east_asian_width(char) in "WF" else 0.6) for char in text)


def _valid_xml(text: str) -> bool:
    return all(char in "\t\n\r" or 0x20 <= ord(char) <= 0xD7FF or 0xE000 <= ord(char) <= 0xFFFD or 0x10000 <= ord(char) <= 0x10FFFF for char in text)


def _string(value: Any, path: str, limit: float, *, optional: bool = False) -> str:
    if not isinstance(value, str) or (not optional and not value.strip()):
        raise ValueError(f"{path} must be a non-empty string")
    if not _valid_xml(value):
        raise ValueError(f"{path} contains a character XML cannot represent")
    if any(char in value for char in "\n\r\t"):
        raise ValueError(f"{path} must be a single line; wrapping is handled by the chart")
    if _em(value) > limit:
        raise ValueError(f"{path} is too long for the chart: maximum {limit:g} CJK-width characters (Latin letters count as 0.6); shorten it or split the chart. No text was truncated.")
    return value


def _number(value: Any, path: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{path} must be a finite number, not a boolean or string")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{path} must be finite; NaN and infinity are not supported")
    # Python integers retain every digit; repr(float) is its round-trip spelling.
    try:
        result = Decimal(str(value))
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{path} is not a representable finite number") from exc
    if len(str(value)) > 24:
        raise ValueError(f"{path} needs more than 24 visible characters; choose a clearly stated smaller unit before charting. No value was rounded or abbreviated.")
    return result


def _display(value: Any) -> str:
    return str(value)


def _decimal_display(value: Decimal) -> str:
    if value == value.to_integral_value():
        return format(value, "f").split(".")[0]
    return format(value, "f").rstrip("0").rstrip(".")


def validate_chart(section: Dict[str, Any], path: str = "chart") -> None:
    """Reject unsupported, misleading or illegible chart input with field paths."""
    if not isinstance(section, dict):
        raise ValueError(f"{path} must be an object")
    unknown = set(section) - _FIELDS
    if unknown:
        raise ValueError(f"{path} has unknown fields: {', '.join(sorted(str(key) for key in unknown))}")
    if section.get("type") != "chart":
        raise ValueError(f"{path}.type must be chart")
    _string(section.get("id"), f"{path}.id", 80)
    _string(section.get("title"), f"{path}.title", 27)
    _string(section.get("source"), f"{path}.source", 49)
    _string(section.get("insight"), f"{path}.insight", 85)
    _string(section.get("unit", ""), f"{path}.unit", 8, optional=True)
    kind = section.get("kind")
    if not isinstance(kind, str) or kind not in _KINDS:
        raise ValueError(f"{path}.kind must be one of {', '.join(_KINDS)}")
    labels = section.get("labels")
    minimum = 2 if kind == "line" else 1
    if not isinstance(labels, list) or not minimum <= len(labels) <= 8:
        raise ValueError(f"{path}.labels must contain {minimum} to 8 labels")
    for index, label in enumerate(labels):
        _string(label, f"{path}.labels[{index}]", 14)
        if kind == "line" and len(_wrap(label, (1152 / len(labels) - 12) / 26)) > 3:
            raise ValueError(f"{path}.labels[{index}] is too long for readable line-chart columns; use fewer points or shorten labels. No label was truncated.")
    if len(set(labels)) != len(labels):
        raise ValueError(f"{path}.labels must be unique so every data point is identifiable")
    series = section.get("series")
    if not isinstance(series, list) or not 1 <= len(series) <= _SERIES_LIMIT[kind]:
        raise ValueError(f"{path}.series for {kind} must contain 1 to {_SERIES_LIMIT[kind]} series")
    names = []
    for index, item in enumerate(series):
        item_path = f"{path}.series[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{item_path} must be an object")
        unknown = set(item) - {"name", "values"}
        if unknown:
            raise ValueError(f"{item_path} has unknown fields: {', '.join(sorted(str(key) for key in unknown))}")
        names.append(_string(item.get("name"), f"{item_path}.name", 14))
        values = item.get("values")
        if not isinstance(values, list) or len(values) != len(labels):
            raise ValueError(f"{item_path}.values length must match labels ({len(labels)})")
        numbers = [_number(value, f"{item_path}.values[{j}]") for j, value in enumerate(values)]
        if kind in {"donut", "funnel", "progress"} and any(value < 0 for value in numbers):
            raise ValueError(f"{item_path}.values for {kind} must be non-negative")
        if kind == "donut" and not any(value > 0 for value in numbers):
            raise ValueError(f"{item_path}.values for donut must have a positive total")
        if kind == "donut":
            with localcontext() as context:
                context.prec = 800
                if _em(_decimal_display(sum(numbers))) * 42 > 260:
                    raise ValueError(f"{path} donut total is too long for the center at readable size; use a clearly stated smaller unit. No total was rounded or abbreviated.")
        if kind == "funnel" and any(right > left for left, right in zip(numbers, numbers[1:])):
            raise ValueError(f"{item_path}.values for funnel must be non-increasing in supplied order")
        if kind == "progress" and any(value > 100 for value in numbers):
            raise ValueError(f"{item_path}.values for progress must be between 0 and 100")
        if kind == "line":
            # Every original value receives a readable column beneath the plot.
            available = 1152 / len(labels) - 14
            for j, value in enumerate(values):
                if _em(_display(value)) * 26 > available:
                    raise ValueError(f"{item_path}.values[{j}] is too long for {len(labels)} line-chart columns at readable size; use fewer points or a clearly stated smaller unit. No value was rounded or abbreviated.")
    if len(set(names)) != len(names):
        raise ValueError(f"{path}.series names must be unique")


def chart_table(section: Dict[str, Any]) -> Tuple[List[str], List[List[str]]]:
    """Return original data for an accessible native document table."""
    validate_chart(section)
    unit = section.get("unit", "")
    suffix = f"（{unit}）" if unit else ""
    headers = ["指标"] + [item["name"] + suffix for item in section["series"]]
    rows = [[label] + [_display(item["values"][index]) for item in section["series"]] for index, label in enumerate(section["labels"])]
    return headers, rows


def _wrap(value: str, max_em: float) -> List[str]:
    lines, line = [], ""
    for char in value:
        if line and _em(line + char) > max_em:
            lines.append(line)
            line = ""
        line += char
    if line:
        lines.append(line)
    return lines or [""]


def _f(value: Any) -> str:
    return f"{float(value):.4f}".rstrip("0").rstrip(".") or "0"


def _tag(tag: str, **attrs: Any) -> str:
    return "<" + tag + " " + " ".join(f'{key.replace("_", "-")}="{escape(str(value), quote=True)}"' for key, value in attrs.items()) + "/>"


def _text(value: str, x: float, y: float, size: int, fill: str, *, weight: int = 400, anchor: str = "start", width: float = 0, line_height: int = 0) -> str:
    lines = _wrap(value, width / size) if width else [value]
    attrs = f'x="{_f(x)}" y="{_f(y)}" font-size="{size}" font-weight="{weight}" fill="{escape(fill, quote=True)}" text-anchor="{anchor}"'
    spans = "".join(f'<tspan x="{_f(x)}" dy="{0 if i == 0 else line_height or round(size * 1.25)}">{escape(line)}</tspan>' for i, line in enumerate(lines))
    return f"<text {attrs}>{spans}</text>"


def _line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: int = 2) -> str:
    return _tag("line", x1=_f(x1), y1=_f(y1), x2=_f(x2), y2=_f(y2), stroke=stroke, stroke_width=width)


def _rect(x: float, y: float, width: float, height: float, fill: str, **attrs: Any) -> str:
    return _tag("rect", x=_f(x), y=_f(y), width=_f(width), height=_f(height), fill=fill, **attrs)


def _theme(theme: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(_DEFAULT_THEME)
    result.update(theme)
    for name in _COLORS:
        if not isinstance(result[name], str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", result[name]):
            raise ValueError(f"theme.{name} must be a six-digit hexadecimal color")
    palette = result["palette"]
    if not isinstance(palette, (list, tuple)) or not palette or any(not isinstance(color, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color) for color in palette):
        raise ValueError("theme.palette must contain six-digit hexadecimal colors")
    return result


def _chrome(section: Dict[str, Any], theme: Dict[str, Any]) -> List[str]:
    primary, secondary, ink = theme["primary"], theme["secondary"], theme["ink"]
    layout = theme.get("layout", "editorial")
    result = [_rect(0, 0, 1600, 900, theme["canvas"])]
    if layout == "ledger":
        result += [_line(70, 42, 1530, 42, primary, 7), _line(70, 57, 1530, 57, primary, 2)]
    elif layout == "nocturne":
        result += [_rect(0, 0, 20, 900, primary), _tag("circle", cx=1510, cy=58, r=24, fill=secondary), _line(1430, 58, 1470, 58, primary, 4)]
    elif layout == "press":
        result += [_rect(70, 37, 65, 12, secondary), _rect(1435, 37, 95, 12, primary)]
    elif layout == "ink":
        result += [_tag("circle", cx=1493, cy=63, r=25, fill=primary), _tag("circle", cx=1493, cy=63, r=16, fill=theme["canvas"]), _line(70, 40, 390, 40, primary, 2)]
    elif layout == "festival":
        result += [_rect(0, 0, 1600, 14, primary), _tag("polygon", points="1460,40 1530,40 1530,110", fill=secondary), _tag("circle", cx=1425, cy=53, r=13, fill=primary)]
    else:
        result += [_rect(70, 36, 8, 70, primary), _line(1410, 46, 1530, 46, secondary, 6)]
    result += [
        _text(_KINDS[section["kind"]], 96, 82, 25, primary, weight=700),
        _text(section["title"], 70, 154, 50, ink, weight=700),
        _line(70, 185, 1530, 185, theme["hairline"]),
        _rect(70, 751, 8, 77, secondary),
        _text("关键洞察", 99, 777, 25, primary, weight=700),
        _text(section["insight"], 252, 777, 28, ink, width=1240, line_height=36),
        _line(70, 842, 1530, 842, theme["hairline"]),
        _text("数据来源", 70, 879, 25, theme["muted"]),
        _text(section["source"], 202, 879, 25, theme["muted"]),
    ]
    return result


def _series_heading(section: Dict[str, Any], theme: Dict[str, Any]) -> str:
    unit = section.get("unit", "")
    result = []
    if section["kind"] == "line":
        result.append(_text("趋势与原始数据", 70, 222, 26, theme["ink"], weight=700))
    elif len(section["series"]) == 1:
        result.append(_text(section["series"][0]["name"], 70, 222, 26, theme["ink"], weight=700))
    else:
        for index, item in enumerate(section["series"]):
            x = 70 + 460 * index
            result += [_rect(x, 203, 14, 21, theme["palette"][index % len(theme["palette"])]), _text(item["name"], x + 26, 223, 26, theme["ink"], weight=700)]
    if unit:
        result.append(_text(f"单位：{unit}", 1530, 222, 25, theme["muted"], anchor="end"))
    return "".join(result)


def _bar(section: Dict[str, Any], theme: Dict[str, Any]) -> List[str]:
    series, labels = section["series"], section["labels"]
    numbers = [[Decimal(str(value)) for value in item["values"]] for item in series]
    flat = [value for values in numbers for value in values]
    low, high = min(min(flat), Decimal(0)), max(max(flat), Decimal(0))
    span = high - low or Decimal(1)
    plot_left, plot_width = 520, 555
    baseline = plot_left + float(-low / span) * plot_width
    result = [_series_heading(section, theme), _line(baseline, 246, baseline, 714, theme["muted"], 2)]
    row = 452 / len(labels)
    bar_height = min(32, (row - 8) / len(series))
    # Label and complete numeric columns remain separate from the encoded area.
    for index, label in enumerate(labels):
        cy = 253 + row * (index + .5)
        result.append(_text(label, 70, cy + 9, 28, theme["ink"]))
        for j, values in enumerate(numbers):
            y = cy - (len(series) * bar_height + (len(series) - 1) * 3) / 2 + j * (bar_height + 3)
            end = plot_left + float((values[index] - low) / span) * plot_width
            color = theme["palette"][j % len(theme["palette"])]
            result.append(_rect(min(baseline, end), y, abs(end - baseline), bar_height, color))
            result.append(_rect(1100, y + bar_height / 2 - 5, 10, 10, color))
            result.append(_text(_display(series[j]["values"][index]), 1510, y + bar_height / 2 + 8, 26, theme["ink"], weight=700, anchor="end"))
    result += [_text("0", baseline, 739, 25, theme["muted"], anchor="middle")]
    return result


def _line_chart(section: Dict[str, Any], theme: Dict[str, Any]) -> List[str]:
    labels, series = section["labels"], section["series"]
    numbers = [[Decimal(str(value)) for value in item["values"]] for item in series]
    flat = [value for values in numbers for value in values]
    low, high = min(min(flat), Decimal(0)), max(max(flat), Decimal(0))
    if low == high:
        high = low + 1
    span = high - low
    cell = 1152 / len(labels)
    xs = [354 + cell * (i + .5) for i in range(len(labels))]
    table_row = 56 if any(_em(item["name"]) > 10 for item in series) else 40
    table_top = 733 - len(series) * table_row
    label_lines = max(len(_wrap(label, (cell - 12) / 26)) for label in labels)
    plot_top, plot_bottom = 257, min(492, table_top - 42 - label_lines * 30)
    def y_of(value: Decimal) -> float:
        return plot_bottom - float((value - low) / span) * (plot_bottom - plot_top)
    result = [_series_heading(section, theme)]
    for fraction in (Decimal(0), Decimal("0.5"), Decimal(1)):
        value = low + fraction * span
        y = y_of(value)
        result.append(_line(xs[0], y, xs[-1], y, theme["hairline"]))
    zero_y = y_of(Decimal(0))
    result += [_line(xs[0], zero_y, xs[-1], zero_y, theme["muted"], 2), _text("0", xs[0] - 20, zero_y + 8, 25, theme["muted"], anchor="end")]
    # Exact data extrema and the explicit zero baseline make the scale inspectable.
    source_values = [value for item in series for value in item["values"]]
    result += [_text("上界", 70, plot_top + 2, 25, theme["muted"]), _text(_display(max(source_values)) if max(flat) > 0 else ("1" if not any(flat) else "0"), 70, plot_top + 36, 26, theme["ink"]), _text("下界", 70, plot_bottom - 34, 25, theme["muted"]), _text(_display(min(source_values)) if min(flat) < 0 else "0", 70, plot_bottom, 26, theme["ink"])]
    for j, values in enumerate(numbers):
        color = theme["palette"][j % len(theme["palette"])]
        points = " ".join(f"{_f(x)},{_f(y_of(value))}" for x, value in zip(xs, values))
        line_style = {"stroke_dasharray": ("14 8" if j == 1 else "3 8")} if j else {}
        result.append(_tag("polyline", points=points, fill="none", stroke=color, stroke_width=4, **line_style))
        for x, value in zip(xs, values):
            result.append(_tag("circle", cx=_f(x), cy=_f(y_of(value)), r=6 + j * 2, fill=theme["surface"], stroke=color, stroke_width=3))
    for x, label in zip(xs, labels):
        lines = _wrap(label, (cell - 12) / 26)
        if len(lines) > 3:
            raise ValueError("chart.labels are too long for readable line-chart columns; use fewer points or shorten labels. No label was truncated.")
        result.append(_text(label, x, plot_bottom + 40, 26, theme["ink"], anchor="middle", width=cell - 12, line_height=30))
    result.append(_line(70, table_top - 12, 1530, table_top - 12, theme["hairline"]))
    for j, item in enumerate(series):
        y = table_top + j * table_row
        color = theme["palette"][j % len(theme["palette"])]
        # A name occupies at most two lines in the narrow series column.
        result.append(_rect(49, y + 10, 10, 10, color))
        result.append(_text(item["name"], 70, y + 24, 26, theme["ink"], weight=700, width=260, line_height=28))
        for x, value in zip(xs, item["values"]):
            result.append(_text(_display(value), x, y + 24, 26, theme["ink"], weight=700, anchor="middle"))
    return result


def _percent_tenths(values: List[Decimal]) -> List[int]:
    """Largest-remainder tenths keep displayed composition totals at 100.0%."""
    total = sum(values)
    exact = [value / total * 1000 for value in values]
    result = [int(value.to_integral_value(rounding=ROUND_FLOOR)) for value in exact]
    remaining = 1000 - sum(result)
    for index in sorted(range(len(values)), key=lambda i: (exact[i] - result[i], -i), reverse=True)[:remaining]:
        result[index] += 1
    return result


def _donut(section: Dict[str, Any], theme: Dict[str, Any]) -> List[str]:
    values = [Decimal(str(value)) for value in section["series"][0]["values"]]
    total, start = sum(values), -math.pi / 2
    total_text = _decimal_display(total)
    if _em(total_text) * 42 > 260:
        raise ValueError("chart donut total is too long for the center at readable size; use a clearly stated smaller unit. No total was rounded or abbreviated.")
    cx, cy, outer, inner = 407, 479, 215, 145
    result = [_series_heading(section, theme), _tag("circle", cx=cx, cy=cy, r=outer, fill=theme["hairline"]), _tag("circle", cx=cx, cy=cy, r=inner, fill=theme["canvas"])]
    percents = _percent_tenths(values)
    for index, value in enumerate(values):
        angle = float(value / total) * math.tau
        # A full circle needs two arcs; every other positive slice needs one.
        if value > 0:
            end = start + angle
            color = theme["palette"][index % len(theme["palette"])]
            def p(radius: float, at: float) -> str:
                return f"{_f(cx + radius * math.cos(at))},{_f(cy + radius * math.sin(at))}"
            if value == total:
                mid = start + math.pi
                d = f"M {p(outer, start)} A {outer},{outer} 0 0 1 {p(outer, mid)} A {outer},{outer} 0 0 1 {p(outer, end)} L {p(inner, end)} A {inner},{inner} 0 0 0 {p(inner, mid)} A {inner},{inner} 0 0 0 {p(inner, start)} Z"
            else:
                large = 1 if angle > math.pi else 0
                d = f"M {p(outer, start)} A {outer},{outer} 0 {large} 1 {p(outer, end)} L {p(inner, end)} A {inner},{inner} 0 {large} 0 {p(inner, start)} Z"
            result.append(_tag("path", d=d, fill=color))
            if angle > .18:
                at = start + angle / 2
                # Identical numbers connect slices to labels without color alone.
                result.append(_tag("circle", cx=_f(cx + 179 * math.cos(at)), cy=_f(cy + 179 * math.sin(at)), r=19, fill=theme["surface"]))
                result.append(_text(str(index + 1), cx + 179 * math.cos(at), cy + 179 * math.sin(at) + 9, 26, theme["ink"], weight=700, anchor="middle"))
            start = end
    result += [_text("合计", cx, cy - 27, 27, theme["muted"], anchor="middle"), _text(total_text, cx, cy + 31, 42, theme["ink"], weight=700, anchor="middle")]
    row = min(67, 452 / len(values))
    start_y = 479 - row * len(values) / 2
    for index, (label, value, percent) in enumerate(zip(section["labels"], section["series"][0]["values"], percents)):
        y = start_y + row * index + row / 2
        color = theme["palette"][index % len(theme["palette"])]
        result += [_tag("circle", cx=727, cy=_f(y), r=18, fill=theme["surface"], stroke=color, stroke_width=3), _text(str(index + 1), 727, y + 9, 26, theme["ink"], weight=700, anchor="middle"), _text(label, 762, y - 3, 27, theme["ink"]), _text(f"{_display(value)}  ·  {percent / 10:.1f}%", 762, y + 25, 25, theme["muted"])]
    return result


def _funnel(section: Dict[str, Any], theme: Dict[str, Any]) -> List[str]:
    values = [Decimal(str(value)) for value in section["series"][0]["values"]]
    maximum = values[0] or Decimal(1)
    row = 454 / len(values)
    center, width = 795, 590
    result = [_series_heading(section, theme)]
    for index, (label, value) in enumerate(zip(section["labels"], values)):
        top, bottom = 250 + index * row, 250 + (index + 1) * row - 7
        top_width = float(value / maximum) * width
        next_value = values[index + 1] if index + 1 < len(values) else value
        bottom_width = float(next_value / maximum) * width
        points = f"{_f(center - top_width / 2)},{_f(top)} {_f(center + top_width / 2)},{_f(top)} {_f(center + bottom_width / 2)},{_f(bottom)} {_f(center - bottom_width / 2)},{_f(bottom)}"
        color = theme["palette"][index % len(theme["palette"])]
        result += [_tag("polygon", points=points, fill=color), _text(label, 70, (top + bottom) / 2 + 9, 28, theme["ink"]), _text(_display(section["series"][0]["values"][index]), 1510, (top + bottom) / 2 + 9, 27, theme["ink"], weight=700, anchor="end")]
    return result


def _progress(section: Dict[str, Any], theme: Dict[str, Any]) -> List[str]:
    row, left, width = 449 / len(section["labels"]), 520, 640
    result = [_series_heading(section, theme), _text("0", left, 265, 25, theme["muted"]), _text("100", left + width, 265, 25, theme["muted"], anchor="end")]
    for index, (label, value) in enumerate(zip(section["labels"], section["series"][0]["values"])):
        cy = 279 + row * (index + .5)
        color = theme["palette"][index % len(theme["palette"])]
        result += [_text(label, 70, cy + 9, 28, theme["ink"]), _rect(left, cy - 12, width, 24, theme["hairline"]), _rect(left, cy - 12, float(Decimal(str(value)) / 100) * width, 24, color), _text(_display(value), 1510, cy + 9, 28, theme["ink"], weight=700, anchor="end")]
    return result


def render_chart_svg(section: Dict[str, Any], theme: Dict[str, Any]) -> str:
    """Render one chart at 1600 by 900 with readable original values and sources."""
    validate_chart(section)
    visual = _theme(theme)
    renderer = {"bar": _bar, "line": _line_chart, "donut": _donut, "funnel": _funnel, "progress": _progress}[section["kind"]]
    # A wide exponent range prevents finite float inputs overflowing coordinates.
    with localcontext() as context:
        context.prec = 800
        parts = _chrome(section, visual) + renderer(section, visual)
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" font-family="Noto Sans SC, sans-serif">' + "".join(parts) + "</svg>"
