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

    def test_rejects_non_string_section_type_with_a_contract_error(self):
        body = minimal_body()
        body["sections"][0]["type"] = []

        with self.assertRaisesRegex(BodyValidationError, "(?i)type"):
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

    def test_rejects_path_unsafe_section_id(self):
        body = standard_body()
        body["sections"][0]["id"] = "../../escaped"

        with self.assertRaisesRegex(BodyValidationError, "(?i)(id|safe)"):
            validate_body(body)

    def test_rejects_missing_fields_for_a_supported_section(self):
        body = standard_body()
        metrics = next(
            section for section in body["sections"] if section["type"] == "metrics"
        )
        del metrics["items"]

        with self.assertRaisesRegex(BodyValidationError, "(?i)items"):
            validate_body(body)

    def test_rejects_table_rows_with_the_wrong_width(self):
        body = standard_body()
        table = next(
            section for section in body["sections"] if section["type"] == "table"
        )
        table["rows"][0].pop()

        with self.assertRaisesRegex(BodyValidationError, "(?i)(row|column|width)"):
            validate_body(body)

    def test_rejects_unknown_fields_instead_of_silently_ignoring_them(self):
        body = standard_body()
        body["sections"][0]["unrendered_business_fact"] = "不能静默丢失"

        with self.assertRaisesRegex(BodyValidationError, "(?i)(unknown|unsupported)"):
            validate_body(body)


if __name__ == "__main__":
    unittest.main()
