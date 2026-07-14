"""Document Body loading and structural validation."""

from __future__ import annotations

import re
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


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
ROOT_KEYS = frozenset({"schema_version", "meta", "theme", "sections", "assets"})
META_KEYS = frozenset({"title", "subtitle", "audience", "status", "reading_time"})
SECTION_KEYS = {
    "callout": frozenset({"id", "type", "title", "tone", "body"}),
    "metrics": frozenset({"id", "type", "title", "items"}),
    "table": frozenset({"id", "type", "title", "columns", "rows"}),
    "grid": frozenset({"id", "type", "title", "items"}),
    "whiteboard_workflow": frozenset({"id", "type", "title", "steps"}),
    "actions": frozenset({"id", "type", "title", "items"}),
}


def _reject_unknown_keys(value: Dict[str, Any], allowed: frozenset, path: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise BodyValidationError(f"unsupported fields at {path}: {', '.join(unknown)}")


def _required_text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BodyValidationError(f"{path} must be a non-empty string")
    return value


def _required_list(value: Any, path: str) -> list:
    if not isinstance(value, list) or not value:
        raise BodyValidationError(f"{path} must be a non-empty list")
    return value


def _validate_item(
    item: Any, *, path: str, required_keys: frozenset
) -> Dict[str, Any]:
    if not isinstance(item, dict):
        raise BodyValidationError(f"{path} must be an object")
    _reject_unknown_keys(item, required_keys, path)
    for key in required_keys:
        _required_text(item.get(key), f"{path}.{key}")
    return item


def _validate_section(section: Dict[str, Any], index: int) -> None:
    path = f"sections[{index}]"
    section_type = section["type"]
    _reject_unknown_keys(section, SECTION_KEYS[section_type], path)
    _required_text(section.get("title"), f"{path}.title")

    if section_type == "callout":
        _required_text(section.get("body"), f"{path}.body")
        tone = section.get("tone", "info")
        if tone not in {"success", "warning", "risk", "info"}:
            raise BodyValidationError(f"{path}.tone is unsupported: {tone!r}")
        return

    if section_type in {"metrics", "grid", "actions"}:
        items = _required_list(section.get("items"), f"{path}.items")
        item_keys = {
            "metrics": frozenset({"label", "value", "note"}),
            "grid": frozenset({"title", "body"}),
            "actions": frozenset({"owner", "action", "due"}),
        }[section_type]
        for item_index, item in enumerate(items):
            _validate_item(
                item,
                path=f"{path}.items[{item_index}]",
                required_keys=item_keys,
            )
        return

    if section_type == "table":
        columns = _required_list(section.get("columns"), f"{path}.columns")
        for column_index, column in enumerate(columns):
            _required_text(column, f"{path}.columns[{column_index}]")
        rows = _required_list(section.get("rows"), f"{path}.rows")
        for row_index, row in enumerate(rows):
            row_path = f"{path}.rows[{row_index}]"
            if not isinstance(row, list) or len(row) != len(columns):
                raise BodyValidationError(
                    f"{row_path} width must match {len(columns)} table columns"
                )
            for cell_index, cell in enumerate(row):
                _required_text(cell, f"{row_path}[{cell_index}]")
        return

    if section_type == "whiteboard_workflow":
        steps = _required_list(section.get("steps"), f"{path}.steps")
        if len(steps) > 6:
            raise BodyValidationError(f"{path}.steps supports at most six items")
        seen_step_ids = set()
        for step_index, step in enumerate(steps):
            step_path = f"{path}.steps[{step_index}]"
            validated = _validate_item(
                step,
                path=step_path,
                required_keys=frozenset({"id", "title", "description"}),
            )
            step_id = validated["id"]
            if not SAFE_ID.fullmatch(step_id):
                raise BodyValidationError(f"{step_path}.id is not a safe identifier")
            if step_id in seen_step_ids:
                raise BodyValidationError(f"duplicate workflow step id: {step_id}")
            seen_step_ids.add(step_id)


def validate_body(body: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a v0.1 Document Body and return the same object.

    Validation fails loudly for unsupported sections so content can never be
    discarded silently by a renderer.
    """

    if not isinstance(body, dict):
        raise BodyValidationError("body must be an object")
    _reject_unknown_keys(body, ROOT_KEYS, "body")
    if body.get("schema_version") != "0.1":
        raise BodyValidationError("schema_version must be 0.1")

    meta = body.get("meta")
    if not isinstance(meta, dict):
        raise BodyValidationError("meta must be an object")
    _reject_unknown_keys(meta, META_KEYS, "meta")
    _required_text(meta.get("title"), "meta.title")
    for optional_key in ("subtitle", "status", "reading_time"):
        if optional_key in meta:
            _required_text(meta[optional_key], f"meta.{optional_key}")
    if "audience" in meta:
        audience = _required_list(meta["audience"], "meta.audience")
        for audience_index, member in enumerate(audience):
            _required_text(member, f"meta.audience[{audience_index}]")

    if "theme" in body:
        _required_text(body["theme"], "theme")

    sections = body.get("sections")
    if not isinstance(sections, list) or not sections:
        raise BodyValidationError("sections must be a non-empty list")

    seen_ids = set()
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise BodyValidationError(f"sections[{index}] must be an object")

        section_id = section.get("id")
        _required_text(section_id, f"sections[{index}].id")
        if not SAFE_ID.fullmatch(section_id):
            raise BodyValidationError(
                f"sections[{index}].id is not a safe identifier"
            )
        if section_id in seen_ids:
            raise BodyValidationError(
                f"section ids must be unique; duplicate id: {section_id}"
            )
        seen_ids.add(section_id)

        section_type = section.get("type")
        if not isinstance(section_type, str) or section_type not in SUPPORTED_SECTION_TYPES:
            raise BodyValidationError(
                f"unsupported section type: {section_type!r}"
            )
        _validate_section(section, index)

    assets = body.get("assets", [])
    if not isinstance(assets, list):
        raise BodyValidationError("assets must be a list")

    return body
