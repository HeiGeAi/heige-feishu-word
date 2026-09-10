"""Content, portability and injection boundaries of the offline HTML outputs."""

from copy import deepcopy
from html.parser import HTMLParser
import unittest

from heige_feishu_word.presets import PRESETS
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
        self._hidden = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in {"script", "style"}:
            self._hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._hidden -= 1

    def handle_data(self, data):
        if not self._hidden:
            self.content.append(data)

    @property
    def text(self):
        return " ".join(self.content)


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

    def test_overview_contains_all_metadata_and_first_metrics_without_controls(self):
        body = deepcopy(PRESETS["executive-brief"]["body"])
        body["sections"].append({
            "id": "extra-metrics", "type": "metrics", "title": "第二组指标不进概览",
            "items": [{"label": "第二组独立标签", "value": "1", "note": "只保留于正文"}],
        })
        html = render_overview_html(body)
        document = _Document(html)
        for key, value in body["meta"].items():
            for text in value if isinstance(value, list) else [value]:
                self.assertIn(text, document.text, key)
        self.assertIn("申请预算", document.text)
        self.assertNotIn("第二组独立标签", document.text)
        self.assertFalse(any(tag in {"button", "a", "script", "dialog", "nav"} for tag, _ in document.tags))
        metadata = {attrs.get("name"): attrs.get("content") for tag, attrs in document.tags if tag == "meta"}
        self.assertEqual(metadata["use-iframe"], "true")
        self.assertEqual(metadata["html-box-height-mode"], "auto")
        self.assertLess(len(html.encode("utf-8")), 500_000)

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


if __name__ == "__main__":
    unittest.main()
