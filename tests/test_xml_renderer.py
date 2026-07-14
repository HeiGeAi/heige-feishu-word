"""Behavior contract for Feishu XML rendering."""

import unittest

from heige_feishu_word.xml_renderer import render_document_xml

from tests.fixtures import standard_body


class DocumentXmlRendererTests(unittest.TestCase):
    def test_renders_semantic_blocks_and_embedded_whiteboard(self):
        xml = render_document_xml(standard_body())

        self.assertIn("<callout", xml)
        self.assertIn("<table>", xml)
        self.assertIn('<whiteboard type="svg">', xml)
        self.assertIn("</whiteboard>", xml)
        self.assertIn("统一 Document Body", xml)

    def test_preserves_critical_text_from_all_six_section_types(self):
        xml = render_document_xml(standard_body())

        anchors = (
            "建议先用统一 Document Body",
            "关键文本回读命中率",
            "模型无关编译器",
            "原生 block 承载正文",
            "内容预整理",
            "产品负责人",
        )
        for anchor in anchors:
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, xml)


if __name__ == "__main__":
    unittest.main()
