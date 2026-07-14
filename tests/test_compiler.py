"""Behavior contract for compiling a complete artifact bundle."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from heige_feishu_word.compiler import compile_body
from heige_feishu_word.model import BodyValidationError

from tests.fixtures import standard_body


class BodyCompilerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.output_dir = Path(self.temporary_directory.name) / "standard-sample"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_compile_writes_complete_artifact_bundle(self):
        body = standard_body()

        manifest = compile_body(body, self.output_dir)

        self.assertEqual(manifest["schema_version"], "0.1")
        expected_files = (
            self.output_dir / "document.xml",
            self.output_dir / "source.body.json",
            self.output_dir / "manifest.json",
            self.output_dir / "boards" / "delivery-workflow.svg",
        )
        for path in expected_files:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 0, path)

        written_body = json.loads(
            (self.output_dir / "source.body.json").read_text(encoding="utf-8")
        )
        written_manifest = json.loads(
            (self.output_dir / "manifest.json").read_text(encoding="utf-8")
        )
        document_xml = (self.output_dir / "document.xml").read_text(encoding="utf-8")
        workflow_svg = (
            self.output_dir / "boards" / "delivery-workflow.svg"
        ).read_text(encoding="utf-8")

        self.assertEqual(written_body, body)
        self.assertEqual(written_manifest, manifest)
        self.assertIn("企业 AI 文档交付引擎 MVP 决策简报", document_xml)
        self.assertIn('viewBox="0 0 1600 900"', workflow_svg)

    def test_rejects_assets_instead_of_silently_dropping_them(self):
        body = standard_body()
        body["assets"] = [{"id": "source-deck", "path": "briefing.pptx"}]

        with self.assertRaisesRegex(BodyValidationError, "asset"):
            compile_body(body, self.output_dir)

        self.assertFalse(self.output_dir.exists())


if __name__ == "__main__":
    unittest.main()
