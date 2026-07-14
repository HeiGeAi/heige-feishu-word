"""Behavior contract for the dependency-free command line interface."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from heige_feishu_word.cli import main

from tests.fixtures import standard_body


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.body_path = self.root / "body.json"
        self.body_path.write_text(
            json.dumps(standard_body(), ensure_ascii=False), encoding="utf-8"
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_validate_prints_machine_readable_success(self):
        stdout = StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["validate", str(self.body_path)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["title"], standard_body()["meta"]["title"])

    def test_compile_writes_bundle_and_reports_output_path(self):
        output_dir = self.root / "compiled"
        stdout = StringIO()

        with redirect_stdout(stdout):
            exit_code = main(
                ["compile", str(self.body_path), "--output", str(output_dir)]
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["output"], str(output_dir.resolve()))
        self.assertEqual(payload["manifest"]["schema_version"], "0.1")
        self.assertTrue((output_dir / "document.xml").is_file())

    def test_compile_reports_an_oversized_board_description_as_json(self):
        body = standard_body()
        workflow = next(
            section
            for section in body["sections"]
            if section["type"] == "whiteboard_workflow"
        )
        workflow["steps"][0]["description"] = "超长画板说明" * 40
        self.body_path.write_text(
            json.dumps(body, ensure_ascii=False), encoding="utf-8"
        )
        stderr = StringIO()

        with redirect_stderr(stderr):
            exit_code = main(
                ["compile", str(self.body_path), "--output", str(self.root / "bad")]
            )

        payload = json.loads(stderr.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertFalse(payload["ok"])
        self.assertIn("too long", payload["error"])


if __name__ == "__main__":
    unittest.main()
