"""Old valid metric content remains complete when a compact figure cannot fit."""

import copy
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from heige_feishu_word.compiler import compile_body, sha256_file
from heige_feishu_word.cover import _wrap, render_metrics_svg, render_metrics_svg_or_none
from heige_feishu_word.model import BodyValidationError, validate_body
from heige_feishu_word.themes import get_theme


def metrics_body(count=4):
    return {
        "schema_version": "0.1", "meta": {"title": "兼容性报告"},
        "sections": [{"id": "metrics-main", "type": "metrics", "title": "指标汇总", "items": [
            {"label": f"指标第{i}项", "value": f"{i}.125%", "note": f"第{i}项的完整业务口径。"}
            for i in range(1, count + 1)
        ]}], "assets": [],
    }


class _VisibleHtml(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.chunks = []
        self.feed(html)

    def handle_data(self, data):
        self.chunks.append(data)


class MetricsCompatibilityTests(unittest.TestCase):
    def assert_complete_bundle(self, output, manifest):
        expected = {record["path"] for record in manifest["artifacts"]} | {"manifest.json"}
        actual = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
        self.assertEqual(actual, expected)
        for record in manifest["artifacts"]:
            self.assertEqual(sha256_file(output / record["path"]), record["sha256"])

    def assert_fallback_preserves_content(self, body):
        validate_body(body)
        with TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            manifest = compile_body(body, output)
            root = ET.fromstring("<doc>" + (output / "document.xml").read_text() + "</doc>")
            native = "".join(root.itertext())
            preview = "".join(_VisibleHtml((output / "preview.html").read_text()).chunks)
            normal = lambda value: "".join(value.split())
            for item in body["sections"][0]["items"]:
                for value in item.values():
                    self.assertIn(normal(value), normal(native))
                    self.assertIn(normal(value), normal(preview))
            self.assertEqual(len(root.findall("table")), 1)
            self.assertEqual(len(root.findall(".//tbody/tr")), len(body["sections"][0]["items"]))
            self.assertFalse(root.findall("whiteboard"))
            self.assertEqual(manifest["board_ids"], [])
            self.assertFalse((output / "boards").exists())
            self.assertFalse((output / "document.enhanced.xml").exists())
            self.assertFalse((output / "widgets").exists())
            self.assert_complete_bundle(output, manifest)
            self.assertEqual(compile_body(body, output), manifest)

    def test_nine_existing_metrics_compile_to_complete_native_table(self):
        self.assert_fallback_preserves_content(metrics_body(9))

    def test_long_label_note_and_value_compile_without_truncation(self):
        for field, value in (
            ("label", "这是一项必须完整保留的指标名称与定义" * 4),
            ("note", '完整口径包括 A < B、C & D、全部样本和排除条件。' * 5),
            ("value", "1234567890123456789012345678901234567890.125%"),
        ):
            body = metrics_body()
            body["sections"][0]["items"][0][field] = value
            with self.subTest(field=field):
                self.assert_fallback_preserves_content(body)

    def test_strict_renderer_still_rejects_capacity_and_helper_does_not_hide_bad_input(self):
        theme = get_theme()
        section = metrics_body(9)["sections"][0]
        with self.assertRaises(BodyValidationError):
            render_metrics_svg(section, theme)
        self.assertIsNone(render_metrics_svg_or_none(section, theme))
        for bad in (None, "", 12, "invalid\x00xml"):
            invalid = copy.deepcopy(section)
            invalid["items"][0]["value"] = bad
            with self.subTest(value=bad), self.assertRaises(BodyValidationError):
                render_metrics_svg_or_none(invalid, theme)
        with self.assertRaises(BodyValidationError):
            render_metrics_svg_or_none({"items": []}, theme)
        with self.assertRaises(KeyError):
            render_metrics_svg_or_none(metrics_body()["sections"][0], {})
        with patch("heige_feishu_word.cover.render_metrics_svg", side_effect=BodyValidationError("unrelated invalid input")):
            with self.assertRaisesRegex(BodyValidationError, "unrelated"):
                render_metrics_svg_or_none(section, theme)

    def test_five_to_eight_metrics_still_render_two_rows_with_every_item(self):
        for count in range(5, 9):
            section = metrics_body(count)["sections"][0]
            svg = render_metrics_svg_or_none(section, get_theme())
            root = ET.fromstring(svg)
            visible = "".join(root.itertext())
            with self.subTest(count=count):
                self.assertEqual(root.attrib["height"], "720")
                self.assertEqual(root.attrib["viewBox"], "0 0 1600 720")
                for item in section["items"]:
                    for value in item.values():
                        self.assertIn(value, visible)

    def test_recompile_removes_stale_metric_board_and_enhanced_artifacts(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            compile_body(metrics_body(), output)
            self.assertTrue((output / "document.enhanced.xml").exists())
            self.assertTrue((output / "boards/metrics-main.svg").exists())
            fallback = compile_body(metrics_body(9), output)
            self.assertFalse((output / "document.enhanced.xml").exists())
            self.assertFalse((output / "boards").exists())
            self.assertFalse((output / "widgets").exists())
            self.assert_complete_bundle(output, fallback)
            self.assertEqual(fallback, compile_body(metrics_body(9), output))

    def test_later_valid_metric_group_renders_without_promoting_it_to_overview(self):
        body = metrics_body(9)
        later = metrics_body(3)["sections"][0]
        later["id"], later["title"] = "metrics-later", "后续指标"
        body["sections"].append(later)
        with TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            manifest = compile_body(body, output)
            self.assertEqual(manifest["board_ids"], ["metrics-later"])
            self.assertTrue((output / "boards/metrics-later.svg").exists())
            self.assertFalse((output / "document.enhanced.xml").exists())
            self.assertFalse((output / "widgets").exists())
            self.assert_complete_bundle(output, manifest)

    def test_no_metrics_means_no_overview_or_enhanced_xml(self):
        body = metrics_body()
        body["sections"] = [{"id": "conclusion", "type": "callout", "title": "结论", "body": "全部内容以原生正文呈现。"}]
        with TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            manifest = compile_body(body, output)
            self.assertEqual(manifest["board_ids"], [])
            self.assertFalse((output / "document.enhanced.xml").exists())
            self.assertFalse((output / "widgets").exists())
            self.assert_complete_bundle(output, manifest)

    def test_orphan_balancing_keeps_both_percentage_tokens_intact(self):
        for token in ("10%", "10％", "72.5%", "72.5％"):
            text = "甲乙" + token + "丙"
            width = 2 + sum(1 if ord(c) > 255 else .6 for c in token) + .1
            lines = _wrap(text, width)
            with self.subTest(token=token):
                self.assertEqual("".join(lines), text)
                self.assertTrue(any(token in line for line in lines), lines)
                self.assertTrue(all(sum(1 if ord(c) > 255 else .6 for c in line) <= width for line in lines))


if __name__ == "__main__":
    unittest.main()
