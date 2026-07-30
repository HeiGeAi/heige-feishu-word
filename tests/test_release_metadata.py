import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_readme_version_matches_pep440_project_version(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        package_init = (ROOT / "src/heige_feishu_word/__init__.py").read_text(encoding="utf-8")
        version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE).group(1)
        package_version = re.search(
            r'^__version__ = "([^"]+)"$', package_init, re.MULTILINE
        ).group(1)

        self.assertRegex(version, r"^0\.1\.0a\d+$")
        self.assertEqual(package_version, version)
        self.assertIn(f"`v{version}`", readme)

    def test_setuptools_license_metadata_uses_current_spdx_form(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('license = "MIT"', pyproject)
        self.assertNotIn('license = {file = "LICENSE"}', pyproject)
        self.assertNotIn("License :: OSI Approved :: MIT License", pyproject)
        self.assertRegex(pyproject, r'setuptools>=([7-9][7-9]|[1-9]\d{2,})')


if __name__ == "__main__":
    unittest.main()
