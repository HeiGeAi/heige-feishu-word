"""Behavior contract for Feishu-safe workflow SVG rendering."""

import unittest

from heige_feishu_word.model import BodyValidationError
from heige_feishu_word.svg_renderer import render_workflow_svg, validate_svg

from tests.fixtures import workflow_section


class WorkflowSvgRendererTests(unittest.TestCase):
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

    def test_workflow_svg_rejects_missing_or_extra_steps_as_body_errors(self):
        section = workflow_section()
        section["steps"] = []

        with self.assertRaises(BodyValidationError):
            render_workflow_svg(section)

        section = workflow_section()
        extra_step = dict(section["steps"][0])
        extra_step["id"] = "extra"
        section["steps"] = section["steps"] + [extra_step]

        with self.assertRaises(BodyValidationError):
            render_workflow_svg(section)

    def test_workflow_svg_wraps_long_step_titles_within_the_card(self):
        section = workflow_section()
        section["steps"][0]["title"] = "统一文档结构与证据整理"  # 11 chars

        svg = render_workflow_svg(section)

        self.assertIn(">统一文档结构与证据整</tspan>", svg)
        self.assertIn(">理</tspan>", svg)

    def test_workflow_svg_rejects_step_titles_that_do_not_fit(self):
        section = workflow_section()
        section["steps"][0]["title"] = "这是一个明显超出卡片标题容量两行预算的超长标题"

        with self.assertRaisesRegex(BodyValidationError, "title"):
            render_workflow_svg(section)

    def test_workflow_svg_rejects_board_titles_that_do_not_fit(self):
        section = workflow_section()
        section["title"] = "这是一个明显超出画板主标题容量单行预算的超长标题会被拒绝"

        with self.assertRaisesRegex(BodyValidationError, "title"):
            render_workflow_svg(section)

    def test_workflow_svg_rejects_descriptions_that_do_not_fit(self):
        section = workflow_section()
        section["steps"][0]["description"] = "这是一段明显超过三行容量的说明文字" * 8

        with self.assertRaisesRegex(ValueError, "(?i)(description|fit|long)"):
            render_workflow_svg(section)


if __name__ == "__main__":
    unittest.main()
