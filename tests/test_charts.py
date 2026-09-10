"""Data and geometric contracts for the chart compiler."""

import copy
from decimal import Decimal
import math
import re
import unittest
from xml.etree import ElementTree as ET

from heige_feishu_word.charts import chart_table, render_chart_svg, validate_chart, _em, _percent_tenths
from heige_feishu_word.svg_renderer import validate_svg


def chart(kind="bar", values=None, labels=None):
    return {"id": "chart-1", "type": "chart", "title": "业务增长来源", "kind": kind,
            "labels": labels or ["华东", "华南", "华北"],
            "series": [{"name": "本期", "values": values if values is not None else [30, 20, 10]}],
            "unit": "万元", "source": "业务台账，2026 年 8 月", "insight": "华东贡献领先，继续核对转化效率。"}


def nodes(svg, tag):
    return ET.fromstring(svg).findall(".//{http://www.w3.org/2000/svg}" + tag)


def data_bars(svg):
    return [node for node in nodes(svg, "rect") if node.attrib.get("id", "").startswith("data-bar-")]


class ChartTests(unittest.TestCase):
    def test_single_series_bar_colors_categories_and_multi_series_colors_series(self):
        palette = ["#245BDD", "#CF582B", "#088976", "#983FA4", "#AC7607", "#C83469", "#27859E", "#557A20"]
        section = chart("bar", [8, 7, 6, 5, 4, 3, 2, 0], list("ABCDEFGH"))
        for embedded in (False, True):
            with self.subTest(embedded=embedded):
                svg = render_chart_svg(section, {"palette": palette}, embedded=embedded)
                bars = data_bars(svg)
                self.assertEqual([bar.attrib["fill"] for bar in bars], palette)
                self.assertEqual([float(bar.attrib["width"]) for bar in bars], [555, 485.625, 416.25, 346.875, 277.5, 208.125, 138.75, 0])
                multiple = copy.deepcopy(section)
                multiple["series"].append({"name": "上期", "values": [1] * 8})
                bars = data_bars(render_chart_svg(multiple, {"palette": palette}, embedded=embedded))
                self.assertEqual([bar.attrib["fill"] for bar in bars], palette[:2] * 8)

    def test_line_uses_distinct_series_colors_and_paired_tints_without_moving_data(self):
        section = chart("line", [-10, 0, 10])
        section["series"].append({"name": "上期", "values": [10, 0, -10]})
        theme = {"palette": ["#245BDD", "#CF582B"], "tints": ["#EEF3FF", "#FFF2EC"]}
        original = copy.deepcopy(theme)
        svg = render_chart_svg(section, theme, embedded=True)
        lines = nodes(svg, "polyline")
        self.assertEqual([line.attrib["stroke"] for line in lines], theme["palette"])
        self.assertNotEqual(lines[0].attrib.get("stroke-dasharray"), lines[1].attrib.get("stroke-dasharray"))
        baseline = nodes(render_chart_svg(section, {}, embedded=True), "polyline")
        self.assertEqual([line.attrib["points"] for line in lines], [line.attrib["points"] for line in baseline])
        for tint in theme["tints"]:
            self.assertTrue(any(node.attrib.get("fill") == tint for node in nodes(svg, "rect")))
        self.assertEqual(theme, original)

    def test_custom_tints_are_validated_before_they_enter_svg(self):
        for value in (None, [], "#FFFFFF", ["red"], ["#FFF"], [12], ['#FFFFFF" onload="alert(1)'], ["url(https://example.com)"]):
            for embedded in (False, True):
                with self.subTest(value=value, embedded=embedded), self.assertRaisesRegex(ValueError, "theme.tints"):
                    render_chart_svg(chart(), {"tints": value}, embedded=embedded)

    def test_embedded_charts_keep_all_data_without_duplicate_document_copy(self):
        for kind in ("bar", "line", "donut", "funnel", "progress"):
            section = chart(kind, [30.25, 20, 0])
            original = copy.deepcopy(section)
            svg = render_chart_svg(section, {}, embedded=True)
            root = ET.fromstring(svg)
            visible = "".join(root.itertext())
            with self.subTest(kind=kind):
                self.assertEqual(root.attrib["height"], "600")
                self.assertEqual(root.attrib["viewBox"], "0 0 1600 600")
                self.assertEqual(validate_svg(svg).errors, ())
                for content in ("本期", "万元", *section["labels"], "30.25", "20", "0"):
                    self.assertIn(content, visible)
                for content in (section["title"], section["source"], section["insight"]):
                    self.assertNotIn(content, visible)
                self.assertEqual(section, original)
                self.assertEqual(render_chart_svg(section, {}), render_chart_svg(section, {}, embedded=False))

    def test_embedded_negative_bars_retain_zero_baseline_and_magnitude(self):
        svg = render_chart_svg(chart("bar", [-20, 40, 0]), {}, embedded=True)
        baseline = next(node for node in nodes(svg, "line") if node.attrib.get("y1") == "246")
        zero = float(baseline.attrib["x1"])
        bars = data_bars(svg)
        self.assertEqual(len(bars), 3)
        self.assertEqual(zero, 705)
        self.assertAlmostEqual(float(bars[0].attrib["x"]) + float(bars[0].attrib["width"]), zero)
        self.assertEqual(float(bars[1].attrib["x"]), zero)
        self.assertEqual(float(bars[2].attrib["width"]), 0)
        self.assertAlmostEqual(float(bars[1].attrib["width"]), 2 * float(bars[0].attrib["width"]))

    def test_embedded_donut_funnel_and_progress_keep_true_proportions(self):
        donut = render_chart_svg(chart("donut", [1, 1, 2]), {}, embedded=True)
        self.assertEqual(len(nodes(donut, "path")), 3)
        self.assertIn("合计4", "".join(ET.fromstring(donut).itertext()))
        self.assertEqual(donut.count("25.0%"), 2)
        self.assertEqual(donut.count("50.0%"), 1)
        funnel = render_chart_svg(chart("funnel", [100, 50, 0]), {}, embedded=True)
        widths = []
        for node in nodes(funnel, "polygon"):
            points = [[float(v) for v in point.split(",")] for point in node.attrib["points"].split()]
            widths.append(points[1][0] - points[0][0])
        self.assertEqual(widths, [590, 295, 0])
        progress = render_chart_svg(chart("progress", [0, 25, 100]), {}, embedded=True)
        bars = [node for node in nodes(progress, "rect") if node.attrib.get("height") == "24" and node.attrib.get("fill") != "#C9D3CC"]
        self.assertEqual([float(node.attrib["width"]) for node in bars], [0, 160, 640])

    def test_dense_embedded_figures_fit_after_the_group_transform(self):
        for kind in ("bar", "line", "donut", "funnel", "progress"):
            section = chart(kind, [80, 70, 60, 50, 40, 30, 20, 10], ["标签名称用于边界布局验证" + str(i) for i in range(8)])
            section["series"][0]["name"] = "系列名称用于边界布局验证"
            if kind in ("bar", "line"):
                section["series"].append({"name": "另一组名称用于边界验证", "values": [10, 20, 30, 40, 50, 60, 70, 80]})
            if kind == "line":
                section["series"].append({"name": "第三组名称用于边界验证", "values": [20, 30, 40, 30, 20, 30, 40, 30]})
            root = ET.fromstring(render_chart_svg(section, {}, embedded=True))
            group = root.find("{http://www.w3.org/2000/svg}g")
            tx, ty = [float(v) for v in re.fullmatch(r"translate\(([-.\d]+) ([-.\d]+)\)", group.attrib["transform"]).groups()]
            boxes = []
            for text in group.findall(".//{http://www.w3.org/2000/svg}text"):
                size, y = float(text.attrib["font-size"]), float(text.attrib["y"]) + ty
                for span in text:
                    x, width = float(span.attrib["x"]) + tx, _em(span.text or "") * size
                    y += float(span.attrib["dy"])
                    anchor = text.attrib.get("text-anchor", "start")
                    x -= width if anchor == "end" else width / 2 if anchor == "middle" else 0
                    boxes.append((x, y - .85 * size, x + width, y + .2 * size, span.text))
            with self.subTest(kind=kind):
                for index, box in enumerate(boxes):
                    self.assertGreaterEqual(box[0], 0, box)
                    self.assertGreaterEqual(box[1], 0, box)
                    self.assertLessEqual(box[2], 1600, box)
                    self.assertLessEqual(box[3], 600, box)
                    for other in boxes[index + 1:]:
                        overlap_x = min(box[2], other[2]) - max(box[0], other[0])
                        overlap_y = min(box[3], other[3]) - max(box[1], other[1])
                        self.assertFalse(overlap_x > 1 and overlap_y > 1, (box[-1], other[-1]))
                if kind == "line":
                    series_lines = group.findall("{http://www.w3.org/2000/svg}polyline")
                    self.assertEqual(len(series_lines), 3)
                    self.assertEqual(len({node.attrib.get("stroke-dasharray", "solid") for node in series_lines}), 3)
                    for node in series_lines:
                        for point in node.attrib["points"].split():
                            x, y = [float(v) for v in point.split(",")]
                            self.assertTrue(0 <= x + tx <= 1600 and 0 <= y + ty <= 600)

    def test_all_chart_types_keep_every_original_value_and_context(self):
        for kind in ("bar", "line", "donut", "funnel", "progress"):
            with self.subTest(kind=kind):
                section = chart(kind, [30.25, 20, 0])
                svg = render_chart_svg(section, {})
                text = "".join(ET.fromstring(svg).itertext())
                for value in [section["title"], section["source"], section["insight"], "万元", "本期", *section["labels"], "30.25", "20", "0"]:
                    self.assertIn(value, text)
                root = ET.fromstring(svg)
                self.assertEqual(root.attrib["viewBox"], "0 0 1600 900")
                self.assertEqual(root.attrib["width"], "1600")
                allowed = {"svg", "g", "rect", "circle", "ellipse", "line", "polyline", "polygon", "path", "text", "tspan"}
                for element in root.iter():
                    self.assertIn(element.tag.rsplit("}", 1)[-1], allowed)
                    self.assertFalse(any(key.startswith("on") or key in {"href", "filter", "mask", "clip-path"} for key in element.attrib))

    def test_native_table_retains_order_precision_unit_and_negative_data(self):
        section = chart("bar", [100.125, -11.5, 0])
        section["series"].append({"name": "上期", "values": [90, -2.25, 1]})
        headers, rows = chart_table(section)
        self.assertEqual(headers, ["指标", "本期（万元）", "上期（万元）"])
        self.assertEqual(rows, [["华东", "100.125", "90"], ["华南", "-11.5", "-2.25"], ["华北", "0", "1"]])

    def test_bar_negative_values_start_at_the_shared_zero_baseline(self):
        svg = render_chart_svg(chart("bar", [-20, 40, 0]), {})
        baseline = next(node for node in nodes(svg, "line") if node.attrib.get("y1") == "246")
        zero_x = float(baseline.attrib["x1"])
        self.assertAlmostEqual(zero_x, 705)
        bars = data_bars(svg)
        self.assertEqual(len(bars), 3)
        first, second, third = bars
        self.assertAlmostEqual(float(first.attrib["x"]) + float(first.attrib["width"]), zero_x)
        self.assertAlmostEqual(float(second.attrib["x"]), zero_x)
        self.assertEqual(float(third.attrib["width"]), 0)
        self.assertAlmostEqual(float(second.attrib["width"]), 2 * float(first.attrib["width"]))

    def test_all_negative_bar_baseline_is_right_boundary(self):
        svg = render_chart_svg(chart("bar", [-4, -2, -1]), {})
        baseline = next(node for node in nodes(svg, "line") if node.attrib.get("y1") == "246")
        self.assertEqual(float(baseline.attrib["x1"]), 1075)

    def test_zero_bar_line_funnel_and_progress_render_without_fake_magnitude(self):
        for kind in ("bar", "line", "funnel", "progress"):
            with self.subTest(kind=kind):
                svg = render_chart_svg(chart(kind, [0, 0, 0]), {})
                self.assertNotRegex(svg, r"(?i)(nan|infinity|\binf\b)")
                if kind == "line":
                    points = nodes(svg, "polyline")[0].attrib["points"].split()
                    self.assertEqual(len(set(point.split(",")[1] for point in points)), 1)
                if kind == "funnel":
                    for polygon in nodes(svg, "polygon"):
                        self.assertEqual(len(set(point.split(",")[0] for point in polygon.attrib["points"].split())), 1)

    def test_line_points_preserve_negative_zero_and_positive_geometry(self):
        svg = render_chart_svg(chart("line", [-10, 0, 10]), {})
        points = [[float(v) for v in point.split(",")] for point in nodes(svg, "polyline")[0].attrib["points"].split()]
        self.assertGreater(points[0][1], points[1][1])
        self.assertGreater(points[1][1], points[2][1])
        self.assertAlmostEqual(points[1][1], (points[0][1] + points[2][1]) / 2)
        self.assertEqual(len(nodes(svg, "circle")), 3)

    def test_donut_uses_true_arc_slices_and_visible_total(self):
        svg = render_chart_svg(chart("donut", [1, 1, 2]), {})
        paths = nodes(svg, "path")
        self.assertEqual(len(paths), 3)
        self.assertTrue(all("A 215,215" in path.attrib["d"] and "A 145,145" in path.attrib["d"] for path in paths))
        text = "".join(ET.fromstring(svg).itertext())
        self.assertIn("合计4", text)
        self.assertIn("25.0%", text)
        self.assertIn("50.0%", text)
        self.assertEqual(_percent_tenths([Decimal(1), Decimal(1), Decimal(1)]), [334, 333, 333])
        self.assertEqual(sum(_percent_tenths([Decimal(1)] * 8)), 1000)

    def test_single_positive_donut_slice_is_a_complete_ring(self):
        svg = render_chart_svg(chart("donut", [7, 0, 0]), {})
        paths = nodes(svg, "path")
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].attrib["d"].count("A 215,215"), 2)
        self.assertEqual(paths[0].attrib["d"].count("A 145,145"), 2)
        self.assertIn("100.0%", svg)

    def test_funnel_stage_widths_follow_exact_values(self):
        svg = render_chart_svg(chart("funnel", [100, 50, 25]), {})
        widths = []
        for polygon in nodes(svg, "polygon"):
            points = [[float(v) for v in point.split(",")] for point in polygon.attrib["points"].split()]
            widths.append(points[1][0] - points[0][0])
        self.assertEqual(widths, [590, 295, 147.5])

    def test_progress_uses_a_fixed_hundred_baseline(self):
        svg = render_chart_svg(chart("progress", [0, 25, 100]), {})
        bars = [node for node in nodes(svg, "rect") if node.attrib.get("height") == "24" and node.attrib.get("fill") != "#C9D3CC"]
        self.assertEqual([float(node.attrib["width"]) for node in bars], [0, 160, 640])

    def test_validation_rejects_invalid_numbers_in_all_positions(self):
        for bad in (True, False, math.nan, math.inf, -math.inf, "12", None, [], {}):
            section = chart(values=[10, bad, 2])
            with self.subTest(value=repr(bad)), self.assertRaisesRegex(ValueError, r"series\[0\]\.values\[1\]"):
                validate_chart(section)

    def test_validation_rejects_missing_provenance_and_unknown_fields(self):
        for field in ("source", "insight", "id", "title"):
            section = chart()
            del section[field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                validate_chart(section)
        section = chart()
        section["hidden_data"] = [1, 2]
        with self.assertRaisesRegex(ValueError, "unknown fields: hidden_data"):
            validate_chart(section)
        section = chart()
        section["series"][0]["unrendered"] = 2
        with self.assertRaisesRegex(ValueError, "unknown fields: unrendered"):
            validate_chart(section)

    def test_validation_rejects_invalid_shapes_and_semantics(self):
        cases = [chart("line", [1], ["A"]), chart("donut", [0, 0, 0]), chart("donut", [-1, 2, 3]), chart("funnel", [2, 3, 1]), chart("progress", [1, 101, 2]), chart("progress", [1, -1, 2])]
        for section in cases:
            with self.subTest(kind=section["kind"], data=section["series"]), self.assertRaises(ValueError):
                validate_chart(section)
        for kind, count in (("bar", 3), ("line", 4), ("donut", 2), ("funnel", 2), ("progress", 2)):
            section = chart(kind)
            section["series"] = [{"name": str(i), "values": [1, 1, 1]} for i in range(count)]
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "series"):
                validate_chart(section)

    def test_labels_and_values_never_silently_truncate(self):
        section = chart()
        section["labels"][0] = "长" * 15
        with self.assertRaisesRegex(ValueError, "No text was truncated"):
            validate_chart(section)
        section["labels"][0] = "长" * 14
        self.assertIn("长" * 14, render_chart_svg(section, {}))
        section = chart("line", [123456789.12345679] * 8, list("ABCDEFGH"))
        with self.assertRaisesRegex(ValueError, "No value was rounded"):
            validate_chart(section)

    def test_xml_text_is_escaped_and_theme_injection_is_rejected(self):
        section = chart()
        section["title"] = 'A < B & "C"'
        section["source"] = "<source>&data"
        section["insight"] = "A > B；请核验。"
        svg = render_chart_svg(section, {})
        text = "".join(ET.fromstring(svg).itertext())
        self.assertIn(section["title"], text)
        self.assertIn(section["source"], text)
        self.assertIn("&lt;source&gt;&amp;data", svg)
        with self.assertRaisesRegex(ValueError, "theme.primary"):
            render_chart_svg(section, {"primary": 'red" onload="evil()'})
        section["source"] = "bad\x00source"
        with self.assertRaisesRegex(ValueError, "XML"):
            validate_chart(section)

    def test_all_layout_signatures_render_and_input_is_unchanged(self):
        section = chart()
        original = copy.deepcopy(section)
        signatures = [render_chart_svg(section, {"layout": layout}) for layout in ("editorial", "ledger", "nocturne", "press", "ink", "festival")]
        self.assertEqual(len(set(signatures)), 6)
        self.assertEqual(section, original)
        for svg in signatures:
            ET.fromstring(svg)

    def test_float_extremes_do_not_overflow_the_plot(self):
        for values in ([-1e308, 0, 1e308], [5e-324, 1e-323, 2e-323]):
            for kind in ("bar", "line"):
                svg = render_chart_svg(chart(kind, values), {})
                self.assertNotRegex(svg, r'="(?:nan|inf|-inf)"')


    def test_dense_charts_have_no_text_collisions_or_canvas_overflow(self):
        # This is deliberately a capacity boundary, not a default short fixture.
        for kind in ("bar", "line", "donut", "funnel", "progress"):
            section = chart(kind, [80, 70, 60, 50, 40, 30, 20, 10], ["标签名称用于边界布局验证" + str(i) for i in range(8)])
            section["series"][0]["name"] = "系列名称用于边界布局验证"
            if kind in ("bar", "line"):
                section["series"].append({"name": "另一组名称用于边界验证", "values": [10, 20, 30, 40, 50, 60, 70, 80]})
            if kind == "line":
                section["series"].append({"name": "第三组名称用于边界验证", "values": [20, 30, 40, 30, 20, 30, 40, 30]})
            boxes = []
            for text in nodes(render_chart_svg(section, {}), "text"):
                size, y = float(text.attrib["font-size"]), float(text.attrib["y"])
                for span in text:
                    x, width = float(span.attrib["x"]), _em(span.text or "") * size
                    y += float(span.attrib["dy"])
                    if text.attrib["text-anchor"] == "end":
                        x -= width
                    elif text.attrib["text-anchor"] == "middle":
                        x -= width / 2
                    boxes.append((x, y - .85 * size, x + width, y + .2 * size, span.text))
            with self.subTest(kind=kind):
                for index, left in enumerate(boxes):
                    self.assertGreaterEqual(left[0], 0, left)
                    self.assertGreaterEqual(left[1], 0, left)
                    self.assertLessEqual(left[2], 1600, left)
                    self.assertLessEqual(left[3], 900, left)
                    for right in boxes[index + 1:]:
                        overlap_x = min(left[2], right[2]) - max(left[0], right[0])
                        overlap_y = min(left[3], right[3]) - max(left[1], right[1])
                        self.assertFalse(overlap_x > 1 and overlap_y > 1, (left[-1], right[-1]))


if __name__ == "__main__":
    unittest.main()
