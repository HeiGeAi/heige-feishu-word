"""Content, portability and injection boundaries of the offline HTML outputs."""

from copy import deepcopy
from html.parser import HTMLParser
import re
import unittest
from xml.etree import ElementTree as ET

from heige_feishu_word.presets import PRESETS
from heige_feishu_word.themes import get_theme
from heige_feishu_word.preview import (
    render_gallery_html,
    render_overview_html,
    render_preview_html,
)


class _Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.content = []
        self.native_content = []
        self.headings = []
        self._heading = None
        self._heading_text = []
        self._svg = 0
        self._hidden = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in {"script", "style", "head"}:
            self._hidden += 1
        if tag == "svg":
            self._svg += 1
        if tag in {"h1", "h2", "h3"}:
            self._heading, self._heading_text = tag, []

    def handle_endtag(self, tag):
        if tag in {"script", "style", "head"}:
            self._hidden -= 1
        if tag == "svg":
            self._svg -= 1
        if tag == self._heading:
            self.headings.append((tag, "".join(self._heading_text)))
            self._heading = None

    def handle_data(self, data):
        if not self._hidden:
            self.content.append(data)
            if not self._svg:
                self.native_content.append(data)
        if self._heading:
            self._heading_text.append(data)

    @property
    def text(self):
        return " ".join(self.content)

    @property
    def native_text(self):
        return " ".join(self.native_content)


class PreviewTests(unittest.TestCase):
    def test_every_preset_keeps_metadata_and_all_section_content(self):
        seen_kinds = set()
        for slug, preset in PRESETS.items():
            body = preset["body"]
            with self.subTest(slug=slug):
                document = _Document(render_preview_html(body))
                for key, value in body["meta"].items():
                    for text in value if isinstance(value, list) else [value]:
                        self.assertIn(text, document.text, key)
                for section in body["sections"]:
                    kind = section["type"]
                    seen_kinds.add(kind)
                    self.assertIn(section["title"], document.text)
                    if kind == "chart":
                        self.assertIn(section["source"], document.text)
                        self.assertIn(section["insight"], document.text)
                        for label in section["labels"]:
                            self.assertIn(label, document.text)
                        for series in section["series"]:
                            self.assertIn(series["name"], document.text)
                            for value in series["values"]:
                                self.assertIn(str(value), document.text)
                    elif kind == "comparison":
                        self.assertIn(section["recommendation"], document.text)
                        for row in section["criteria"]:
                            for text in [row["label"]] + row["values"]:
                                self.assertIn(text, document.text)
                    elif kind == "table":
                        for text in section["columns"] + [c for row in section["rows"] for c in row]:
                            self.assertIn(text, document.text)
                    elif kind == "prose":
                        for text in section["paragraphs"]:
                            self.assertIn(text, document.text)
                    elif kind == "callout":
                        self.assertIn(section["body"], document.text)
                    else:
                        for item in section.get("items", section.get("steps", [])):
                            for key, text in item.items():
                                if key not in {"id", "status"}:
                                    self.assertIn(text, document.text)
                section_ids = [attrs["id"] for tag, attrs in document.tags if tag == "section"]
                self.assertEqual(len(section_ids), len(body["sections"]))
                self.assertEqual(len(set(section_ids)), len(section_ids))
                for tag, attrs in document.tags:
                    for attribute in ("href", "src"):
                        if attribute in attrs:
                            self.assertFalse(attrs[attribute].startswith(("http:", "https:", "//")))
        self.assertEqual(seen_kinds, {"callout", "metrics", "table", "grid", "actions", "prose", "chart", "timeline", "comparison", "whiteboard_workflow"})

    def test_user_markup_is_text_including_titles_and_metadata(self):
        attack = '<script>alert("unsafe")</script><img src=x onerror=alert(1)>'
        body = {
            "schema_version": "0.2", "theme": "moxi-void",
            "meta": {"title": attack, "subtitle": attack, "status": attack, "disclaimer": attack},
            "sections": [{"id": "copy", "type": "prose", "title": attack, "paragraphs": [attack]}],
        }
        document = _Document(render_preview_html(body))
        self.assertIn(attack, document.text)
        self.assertFalse(any(tag == "img" for tag, _ in document.tags))
        self.assertEqual(sum(tag == "script" for tag, _ in document.tags), 1)
        self.assertFalse(any(any(key.startswith("on") for key in attrs) for _, attrs in document.tags))

    def test_overview_contains_only_first_metric_group_without_repeating_native_chrome(self):
        body = deepcopy(PRESETS["executive-brief"]["body"])
        body["sections"].append({
            "id": "extra-metrics", "type": "metrics", "title": "第二组指标不进概览",
            "items": [{"label": "第二组独立标签", "value": "1", "note": "只保留于正文"}],
        })
        html = render_overview_html(body)
        document = _Document(html)
        for value in body["meta"].values():
            for text in value if isinstance(value, list) else [value]:
                self.assertNotIn(text, document.text)
        metrics = next(section for section in body["sections"] if section["type"] == "metrics")
        for item in metrics["items"]:
            for text in item.values():
                self.assertIn(text, document.text)
        self.assertNotIn(metrics["title"], document.text)
        self.assertNotIn("第二组独立标签", document.text)
        self.assertFalse(any(tag in {"button", "a", "script", "dialog", "nav", "h1", "h2", "header", "footer", "svg"} for tag, _ in document.tags))
        metadata = {attrs.get("name"): attrs.get("content") for tag, attrs in document.tags if tag == "meta"}
        self.assertEqual(metadata["use-iframe"], "true")
        self.assertEqual(metadata["html-box-height-mode"], "auto")
        self.assertLess(len(html.encode("utf-8")), 500_000)

    def test_overview_without_metrics_is_empty_instead_of_a_duplicate_document_cover(self):
        body = deepcopy(PRESETS["decision-memo"]["body"])
        self.assertFalse(any(section["type"] == "metrics" for section in body["sections"]))
        document = _Document(render_overview_html(body))
        self.assertEqual(document.text.strip(), "")
        self.assertFalse(any(tag in {"article", "h1", "h2", "footer"} for tag, _ in document.tags))

    def test_overview_escapes_metric_text_and_has_no_external_resources(self):
        attack = '<img src=x onerror="alert(1)"><script>unsafe()</script>'
        body = deepcopy(PRESETS["executive-brief"]["body"])
        metrics = next(section for section in body["sections"] if section["type"] == "metrics")
        metrics["items"][0] = {"label": attack, "value": attack, "note": attack}
        document = _Document(render_overview_html(body))
        self.assertIn(attack, document.text)
        self.assertFalse(any(tag in {"img", "script", "link"} for tag, _ in document.tags))
        self.assertFalse(any(any(key.startswith("on") for key in attrs) for _, attrs in document.tags))

    def test_white_document_headings_and_chart_evidence_appear_once_in_the_reading_flow(self):
        for slug, preset in PRESETS.items():
            with self.subTest(slug=slug):
                body = preset["body"]
                html = render_preview_html(body)
                document = _Document(html)
                self.assertEqual([heading for heading in document.headings if heading[0] == "h1"], [("h1", body["meta"]["title"])])
                self.assertEqual([heading[1] for heading in document.headings if heading[0] == "h2"], [section["title"] for section in body["sections"]])
                self.assertFalse(any(tag == "nav" for tag, _ in document.tags))
                self.assertNotIn('class="hero"', html)
                self.assertNotIn("background-image:", html)
                self.assertIn("width:min(820px", html)
                self.assertIn("body{margin:0;background:#fff", html)
                charts = [section for section in body["sections"] if section["type"] == "chart"]
                for chart in charts:
                    self.assertEqual(document.native_text.count(chart["insight"]), 1)
                    self.assertEqual(document.native_text.count(chart["source"]), 1)
                for svg in re.findall(r"<svg\b.*?</svg>", html, re.DOTALL):
                    root = ET.fromstring(svg)
                    visible = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "text")
                    self.assertNotIn(body["meta"]["title"], visible)
                    for chart in charts:
                        self.assertNotIn(chart["title"], visible)
                        self.assertNotIn(chart["source"], visible)
                        self.assertNotIn(chart["insight"], visible)

    def test_metrics_have_one_artwork_and_complete_native_text_in_preview(self):
        from heige_feishu_word.cover import render_metrics_svg
        from heige_feishu_word.themes import get_theme

        body = deepcopy(PRESETS["executive-brief"]["body"])
        metrics = next(section for section in body["sections"] if section["type"] == "metrics")
        html = render_preview_html(body)
        document = _Document(html)
        self.assertEqual(html.count(render_metrics_svg(metrics, get_theme(body["theme"]))), 1)
        self.assertFalse(any(attrs.get("class") == "metric-value" for _, attrs in document.tags))
        for item in metrics["items"]:
            for text in item.values():
                self.assertIn(text, document.native_text)

    def test_figure_controls_retain_original_size_fit_escape_and_print_support(self):
        html = render_preview_html(PRESETS["executive-brief"]["body"])
        document = _Document(html)
        attributes = {key for tag, attrs in document.tags if tag == "button" for key in attrs}
        self.assertTrue({"data-actual", "data-enlarge", "data-fit", "data-close", "data-print"}.issubset(attributes))
        self.assertIn("original.viewBox", html)
        self.assertIn("resize(nativeWidth)", html)
        self.assertIn("event.key==='Escape'", html)
        self.assertIn("origin.focus()", html)
        self.assertIn("beforeprint", html)
        self.assertIn("afterprint", html)
        self.assertIn("prefers-reduced-motion:reduce", html)
        self.assertNotIn("innerHTML", html)

    def test_document_accents_alternate_two_colors_and_use_registered_palette_tokens(self):
        for preset in PRESETS.values():
            body = preset["body"]
            theme = get_theme(body["theme"])
            html = render_preview_html(body)
            document = _Document(html)
            section_colors = [attrs["data-color"] for tag, attrs in document.tags if tag == "section"]
            self.assertEqual(section_colors, [str(index % 2) for index in range(len(body["sections"]))])
            self.assertEqual(sum(attrs.get("class") == "header-rule" for _, attrs in document.tags), 1)
            for index in range(8):
                self.assertIn("--color-%d:%s" % (index, theme["palette"][index]), html)
                self.assertIn("--tint-%d:%s" % (index, theme["tints"][index]), html)
            self.assertIn("background:var(--secondary)", html)
            self.assertNotIn("linear-gradient", html)

    def test_eight_metric_overview_uses_four_readable_pairs_without_losing_items(self):
        def luminance(color):
            components = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in components]
            return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

        def contrast(first, second):
            light, dark = sorted((luminance(first), luminance(second)), reverse=True)
            return (light + 0.05) / (dark + 0.05)

        for preset in PRESETS.values():
            body = deepcopy(preset["body"])
            items = [{"label": "指标 %d" % index, "value": str(index * 10), "note": "指标 %d 的口径" % index} for index in range(1, 9)]
            body["sections"] = [{"id": "eight", "type": "metrics", "title": "八项指标", "items": items}]
            html = render_overview_html(body)
            document = _Document(html)
            colors = [attrs["data-color"] for tag, attrs in document.tags if tag == "article"]
            self.assertEqual(colors, [str(index % 4) for index in range(8)])
            self.assertIn(".overview-metric:first-child{background:var(--primary);color:#fff}", html)
            self.assertIn(".overview-metric:first-child:before{background:var(--secondary)}", html)
            theme = get_theme(body["theme"])
            self.assertGreaterEqual(contrast(theme["primary"], "#ffffff"), 4.5)
            for index in range(4):
                self.assertGreaterEqual(contrast(theme["palette"][index], theme["tints"][index]), 4.5)
                self.assertGreaterEqual(contrast(theme["ink"], theme["tints"][index]), 4.5)
            for item in items:
                for text in item.values():
                    self.assertIn(text, document.text)

    def test_semantic_callout_tones_survive_theme_and_accent_changes(self):
        body = deepcopy(PRESETS["launch-story"]["body"])
        tones = {"info": "要点", "success": "结论", "warning": "关注", "risk": "风险"}
        body["sections"] = [
            {"id": tone, "type": "callout", "title": "观察 " + tone, "tone": tone, "body": "完整判断 " + tone}
            for tone in tones
        ]
        document = _Document(render_preview_html(body))
        self.assertEqual([attrs["data-tone"] for tag, attrs in document.tags if tag == "aside"], list(tones))
        for tone, label in tones.items():
            self.assertIn(label, document.text)
            self.assertIn("完整判断 " + tone, document.text)

    def test_gallery_links_are_local_and_untrusted_directory_names_are_rejected(self):
        entries = [dict(slug=slug, **preset) for slug, preset in PRESETS.items()]
        document = _Document(render_gallery_html(entries))
        links = [attrs["href"] for tag, attrs in document.tags if tag == "a"]
        self.assertEqual(links, [entry["slug"] + "/preview.html" for entry in entries])
        self.assertEqual(len(links), 6)
        entries[0]["slug"] = "../../outside"
        with self.assertRaisesRegex(ValueError, "safe local directory"):
            render_gallery_html(entries)

    def test_gallery_names_and_descriptions_cannot_create_elements(self):
        entry = {"slug": "safe", "theme": "atelier-bone", "name": "<img src=x>", "description": "<script>unsafe()</script>"}
        document = _Document(render_gallery_html([entry]))
        self.assertIn(entry["name"], document.text)
        self.assertIn(entry["description"], document.text)
        self.assertFalse(any(tag in {"img", "script"} for tag, _ in document.tags))

    def test_gallery_supplied_theme_dictionary_cannot_inject_css_values(self):
        attack = '</style><script>unsafe()</script>'
        entry = {"slug": "safe", "theme": {"slug": "atelier-bone", "primary": attack, "palette": [attack], "tints": [attack]}, "name": "安全主题", "description": "只使用注册色板"}
        html = render_gallery_html([entry])
        self.assertNotIn(attack, html)
        self.assertIn(get_theme("atelier-bone")["tints"][0], html)
        self.assertFalse(any(tag == "script" for tag, _ in _Document(html).tags))


if __name__ == "__main__":
    unittest.main()
