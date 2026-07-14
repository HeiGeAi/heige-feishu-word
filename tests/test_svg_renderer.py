"""Behavior contract for Feishu-safe workflow SVG rendering."""

import unittest

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


if __name__ == "__main__":
    unittest.main()
