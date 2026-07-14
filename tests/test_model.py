"""Behavior contract for Document Body validation."""

import unittest

from heige_feishu_word.model import BodyValidationError, validate_body

from tests.fixtures import minimal_body, standard_body


class BodyValidationTests(unittest.TestCase):
    def test_accepts_complete_standard_body(self):
        body = standard_body()

        validated = validate_body(body)

        self.assertIs(validated, body)

    def test_rejects_unknown_section_type(self):
        body = minimal_body(section_type="unknown")

        with self.assertRaisesRegex(BodyValidationError, "unknown"):
            validate_body(body)

    def test_rejects_duplicate_section_ids(self):
        body = standard_body()
        body["sections"][1]["id"] = body["sections"][0]["id"]

        with self.assertRaisesRegex(BodyValidationError, "(?i)(duplicate|unique)"):
            validate_body(body)

    def test_rejects_missing_document_title(self):
        body = minimal_body()
        del body["meta"]["title"]

        with self.assertRaisesRegex(BodyValidationError, "(?i)title"):
            validate_body(body)


if __name__ == "__main__":
    unittest.main()
