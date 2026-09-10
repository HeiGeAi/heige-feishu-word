"""Behavior and data-integrity checks for the reusable document catalog."""

import json
import unittest
from xml.etree import ElementTree as ET

from heige_feishu_word.model import validate_body
from heige_feishu_word.presets import PRESETS, get_preset, list_presets
from heige_feishu_word.svg_renderer import validate_svg
from heige_feishu_word.themes import get_theme
from heige_feishu_word.xml_renderer import render_document_xml


class PresetTests(unittest.TestCase):
    def test_catalog_exposes_six_distinct_themes_without_document_payloads(self):
        catalog = list_presets()
        self.assertEqual(len(catalog), 6)
        self.assertEqual(len({item["theme"] for item in catalog}), 6)
        for item in catalog:
            with self.subTest(preset=item["slug"]):
                self.assertEqual(set(item), {"slug", "name", "description", "theme"})
                self.assertEqual(get_theme(item["theme"])["slug"], item["theme"])
                self.assertEqual(get_preset(item["slug"])["theme"], item["theme"])

    def test_personalizing_a_document_does_not_change_the_next_copy(self):
        slug = "executive-brief"
        original = get_preset(slug)
        edited = get_preset(slug)
        edited["meta"]["audience"].append("新的读者")
        edited["meta"]["title"] = "用户自己的业务"
        chart = next(section for section in edited["sections"] if section["type"] == "chart")
        chart["series"][0]["values"][0] = 999
        self.assertEqual(get_preset(slug), original)

    def test_catalog_edits_do_not_change_stored_metadata(self):
        catalog = list_presets()
        first_slug = catalog[0]["slug"]
        catalog[0]["name"] = "用户自定义名字"
        self.assertNotEqual(PRESETS[first_slug]["name"], catalog[0]["name"])

    def test_unknown_or_non_string_slug_reports_a_useful_error(self):
        for slug in ("missing", "", None, [], {}):
            with self.subTest(slug=slug):
                with self.assertRaisesRegex(ValueError, "unsupported preset.*executive-brief"):
                    get_preset(slug)

    def test_every_preset_is_a_valid_complete_document_with_synthetic_disclosure(self):
        kinds = set()
        rhythms = set()
        for slug in PRESETS:
            with self.subTest(preset=slug):
                body = get_preset(slug)
                self.assertIs(validate_body(body), body)
                self.assertEqual(body["schema_version"], "0.2")
                self.assertGreaterEqual(len(body["sections"]), 6)
                self.assertLessEqual(len(body["sections"]), 8)
                self.assertLessEqual(len(body["meta"]["title"]), 20)
                self.assertIn("合成", body["meta"]["subtitle"])
                for term in ("合成", "来源", "数值", "负责人", "日期"):
                    self.assertIn(term, body["meta"]["disclaimer"])
                encoded = json.dumps(body, ensure_ascii=False)
                for forbidden in ("\u2014", "\u2013", "\u002d\u002d", "TODO", "待填写"):
                    self.assertNotIn(forbidden, encoded)
                charts = [section for section in body["sections"] if section["type"] == "chart"]
                self.assertTrue(charts)
                for chart in charts:
                    self.assertIn("合成", chart["source"])
                    self.assertTrue(chart["insight"])
                    self.assertLessEqual(len(chart["title"]), 18)
                    self.assertLessEqual(len(chart["labels"]), 8)
                    self.assertTrue(all(len(label) <= 14 for label in chart["labels"]))
                    kinds.add(chart["kind"])
                for section in body["sections"]:
                    if section["type"] == "whiteboard_workflow":
                        for step in section["steps"]:
                            self.assertLessEqual(len(step["title"]), 11)
                            self.assertLessEqual(len(step["description"]), 40)
                rhythms.add(tuple(section["type"] for section in body["sections"]))
        self.assertEqual(kinds, {"bar", "line", "donut", "funnel", "progress"})
        self.assertEqual(len(rhythms), 6)

    def test_every_preset_renders_valid_boards_and_keeps_native_chart_evidence(self):
        for slug in PRESETS:
            with self.subTest(preset=slug):
                body = get_preset(slug)
                root = ET.fromstring("<document>" + render_document_xml(body) + "</document>")
                for board in root.findall(".//whiteboard"):
                    svg = ET.tostring(list(board)[0], encoding="unicode")
                    self.assertFalse(validate_svg(svg).errors)
                # Removing SVGs models the editable native document layer.
                # Sources and interpretations must remain available there.
                for board in list(root.findall("whiteboard")):
                    root.remove(board)
                native_text = "".join(root.itertext())
                for section in body["sections"]:
                    if section["type"] == "chart":
                        self.assertIn(section["source"], native_text)
                        self.assertIn(section["insight"], native_text)
                        for label in section["labels"]:
                            self.assertIn(label, native_text)

    def test_example_totals_support_the_written_business_narrative(self):
        def chart(slug, section_id):
            return next(section for section in get_preset(slug)["sections"] if section["id"] == section_id)

        allocation = chart("executive-brief", "allocation")["series"][0]["values"]
        self.assertEqual(sum(allocation), 120)
        self.assertEqual(allocation[0] / sum(allocation), 0.5)

        trend = chart("operating-review", "trend")["series"]
        self.assertEqual(sum(trend[0]["values"]), 622)
        self.assertEqual(sum(trend[1]["values"]), 626)
        self.assertEqual(sum(chart("operating-review", "channels")["series"][0]["values"]), 132)

        completion = chart("project-pulse", "completion")["series"][0]["values"]
        self.assertEqual(sum(completion) / len(completion), 72.5)

        estimates = chart("decision-memo", "cost")["series"]
        self.assertEqual(sum(estimates[0]["values"]), 36)
        self.assertEqual(sum(estimates[1]["values"]), 54)

        funnel = chart("launch-story", "conversion")["series"][0]["values"]
        self.assertEqual(funnel, sorted(funnel, reverse=True))
        self.assertAlmostEqual(funnel[-1] / funnel[0], 0.024)
        self.assertAlmostEqual(funnel[-1] / funnel[-2], 0.3)


if __name__ == "__main__":
    unittest.main()
