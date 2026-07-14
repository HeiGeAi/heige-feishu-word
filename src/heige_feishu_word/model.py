"""Document Body loading and structural validation."""

from __future__ import annotations

from typing import Any, Dict


SUPPORTED_SECTION_TYPES = frozenset(
    {
        "callout",
        "metrics",
        "table",
        "grid",
        "whiteboard_workflow",
        "actions",
    }
)


class BodyValidationError(ValueError):
    """Raised when a Document Body violates the public v0.1 contract."""


def validate_body(body: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a v0.1 Document Body and return the same object.

    Validation fails loudly for unsupported sections so content can never be
    discarded silently by a renderer.
    """

    if not isinstance(body, dict):
        raise BodyValidationError("body must be an object")
    if body.get("schema_version") != "0.1":
        raise BodyValidationError("schema_version must be 0.1")

    meta = body.get("meta")
    if not isinstance(meta, dict):
        raise BodyValidationError("meta must be an object")
    if not isinstance(meta.get("title"), str) or not meta["title"].strip():
        raise BodyValidationError("meta.title is required")

    sections = body.get("sections")
    if not isinstance(sections, list) or not sections:
        raise BodyValidationError("sections must be a non-empty list")

    seen_ids = set()
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise BodyValidationError(f"sections[{index}] must be an object")

        section_id = section.get("id")
        if not isinstance(section_id, str) or not section_id.strip():
            raise BodyValidationError(f"sections[{index}].id is required")
        if section_id in seen_ids:
            raise BodyValidationError(
                f"section ids must be unique; duplicate id: {section_id}"
            )
        seen_ids.add(section_id)

        section_type = section.get("type")
        if section_type not in SUPPORTED_SECTION_TYPES:
            raise BodyValidationError(
                f"unsupported section type: {section_type!r}"
            )

    assets = body.get("assets", [])
    if not isinstance(assets, list):
        raise BodyValidationError("assets must be a list")

    return body

