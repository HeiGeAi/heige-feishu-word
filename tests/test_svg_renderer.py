"""Behavior contract for Feishu-safe workflow SVG rendering."""

import unittest
from xml.etree import ElementTree as ET

from heige_feishu_word.svg_renderer import render_workflow_svg, validate_svg, _flow_em

from tests.fixtures import workflow_section


class WorkflowSvgRendererTests(unittest.TestCase):
    def test_embedded_workflow_uses_one_row_for_three_or_four_steps(self):
        for count in (3, 4, 5, 6):
            section = workflow_section()
            section["steps"] = section["steps"][:count]
            svg = render_workflow_svg(section, embedded=True)
            root = ET.fromstring(svg)
            groups = root.findall("{http://www.w3.org/2000/svg}g")
            circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
            with self.subTest(steps=count):
                self.assertEqual(len(groups), count)
                self.assertEqual(len({node.attrib["cy"] for node in circles}), 1 if count <= 4 else 2)
                self.assertLess(int(root.attrib["height"]), 600)
                self.assertEqual(validate_svg(svg).errors, ())
                self.assertNotIn(section["title"], "".join(root.itertext()))
                self.assertNotIn("WORKFLOW", svg)
                self.assertNotIn("HEIGE", svg)
                for step, group in zip(section["steps"], groups):
                    content = "".join(group.itertext())
                    self.assertIn(step["title"], content)
                    self.assertIn(step["description"], content)

    def test_embedded_workflow_preserves_escaped_copy_and_color_literals(self):
        section = workflow_section()
        section["steps"] = section["steps"][:4]
        section["steps"][0]["title"] = "比较 A&B"
        section["steps"][0]["description"] = '保留 #FFFFFF 色值，A < B，\"原文\" 不改。'
        root = ET.fromstring(render_workflow_svg(section, embedded=True))
        group = root.find("{http://www.w3.org/2000/svg}g")
        content = "".join(group.itertext())
        self.assertIn(section["steps"][0]["title"], content)
        self.assertIn(section["steps"][0]["description"], content)

    def test_embedded_workflow_capacity_has_no_text_overlap_or_clipping(self):
        for count in (4, 6):
            section = workflow_section()
            section["steps"] = section["steps"][:count]
            for step in section["steps"]:
                step["title"] = "评审后确认上线范围"
                step["description"] = "评审通过后释放余款，未通过则调整方案。完成续费体验改版，记录适用客户范围。"
            root = ET.fromstring(render_workflow_svg(section, embedded=True))
            height = int(root.attrib["height"])
            boxes = []
            for text in root.findall(".//{http://www.w3.org/2000/svg}text"):
                size, y = float(text.attrib["font-size"]), float(text.attrib["y"])
                spans = list(text) or [text]
                for span in spans:
                    x = float(span.attrib["x"])
                    y += float(span.attrib.get("dy", 0))
                    width = _flow_em(span.text or "") * size
                    if text.attrib.get("text-anchor") == "middle":
                        x -= width / 2
                    boxes.append((x, y - .85 * size, x + width, y + .2 * size, span.text))
            with self.subTest(steps=count):
                self.assertEqual(validate_svg(ET.tostring(root, encoding="unicode")).errors, ())
                for index, box in enumerate(boxes):
                    self.assertGreaterEqual(box[0], 0, box)
                    self.assertGreaterEqual(box[1], 0, box)
                    self.assertLessEqual(box[2], 1600, box)
                    self.assertLessEqual(box[3], height, box)
                    for other in boxes[index + 1:]:
                        overlap_x = min(box[2], other[2]) - max(box[0], other[0])
                        overlap_y = min(box[3], other[3]) - max(box[1], other[1])
                        self.assertFalse(overlap_x > 1 and overlap_y > 1, (box[-1], other[-1]))

    def test_embedded_workflow_rejects_over_capacity_without_truncation(self):
        for description in ("超出可读容量的完整说明" * 20, "UnbreakableLatinWord" * 8):
            section = workflow_section()
            section["steps"][0]["description"] = description
            with self.subTest(description=description), self.assertRaisesRegex(ValueError, "(?i)no text was truncated"):
                render_workflow_svg(section, embedded=True)

    def test_embedded_workflow_keeps_default_standalone_contract(self):
        section = workflow_section()
        self.assertEqual(render_workflow_svg(section), render_workflow_svg(section, embedded=False))

    def test_svg_validator_accepts_document_heights_with_matching_viewboxes(self):
        for height in (240, 380, 600, 720, 900, 1000):
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}"/>'
            with self.subTest(height=height):
                self.assertEqual(validate_svg(svg).errors, ())
                self.assertTrue(validate_svg(svg.replace(f'viewBox="0 0 1600 {height}"', 'viewBox="0 0 1600 999"')).errors)
        for height in ("239", "1001", "600.5", "nan", ""):
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}"/>'
            with self.subTest(height=height):
                self.assertTrue(validate_svg(svg).errors)

    def test_workflow_svg_is_feishu_safe_and_uses_fixed_canvas(self):
        svg = render_workflow_svg(workflow_section())

        report = validate_svg(svg)

        self.assertEqual(report.errors, ())
        self.assertIn('width="1600"', svg)
        self.assertIn('height="900"', svg)
        self.assertIn('viewBox="0 0 1600 900"', svg)

    def test_workflow_svg_contains_every_step(self):
        section = workflow_section()

        svg = render_workflow_svg(section)

        self.assertIn(section["title"], svg)
        for step in section["steps"]:
            with self.subTest(step=step["id"]):
                self.assertIn(step["title"], svg)

    def test_workflow_svg_does_not_split_latin_words(self):
        section = workflow_section()
        section["steps"][0]["description"] = "文字、会议纪要、图片、PDF、Word、PPT"

        svg = render_workflow_svg(section)

        self.assertIn(">Word、PPT</tspan>", svg)
        self.assertNotIn(">Wo</tspan>", svg)

    def test_workflow_svg_rejects_descriptions_that_do_not_fit(self):
        section = workflow_section()
        section["steps"][0]["description"] = "这是一段明显超过三行容量的说明文字" * 8

        with self.assertRaisesRegex(ValueError, "(?i)(description|fit|long)"):
            render_workflow_svg(section)


if __name__ == "__main__":
    unittest.main()
