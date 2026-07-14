"""Compile a Document Body into a deterministic local artifact bundle."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .model import BodyValidationError, validate_body
from .svg_renderer import render_workflow_svg, validate_svg
from .xml_renderer import render_document_xml


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all at once."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _artifact_record(root: Path, path: Path, role: str) -> Dict[str, Any]:
    return {
        "role": role,
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _workflow_sections(body: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    return (
        section
        for section in body["sections"]
        if section["type"] == "whiteboard_workflow"
    )


def compile_body(body: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    """Compile a Body into XML, board SVGs, source JSON, and a manifest."""

    validate_body(body)
    if body.get("assets"):
        raise BodyValidationError(
            "the standard-sample compiler does not ingest assets yet; no asset was dropped"
        )
    output_dir = Path(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary_dir = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=str(output_dir.parent))
    )
    try:
        source_path = temporary_dir / "source.body.json"
        document_path = temporary_dir / "document.xml"
        _write_text(
            source_path,
            json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        _write_text(document_path, render_document_xml(body))

        artifacts: List[Dict[str, Any]] = [
            _artifact_record(temporary_dir, source_path, "source_body"),
            _artifact_record(temporary_dir, document_path, "feishu_xml"),
        ]
        board_ids: List[str] = []
        for section in _workflow_sections(body):
            board_id = section["id"]
            board_path = temporary_dir / "boards" / f"{board_id}.svg"
            svg = render_workflow_svg(section)
            report = validate_svg(svg)
            if report.errors:
                raise BodyValidationError(
                    f"invalid SVG for {board_id}: {'; '.join(report.errors)}"
                )
            _write_text(board_path, svg + "\n")
            artifacts.append(
                _artifact_record(temporary_dir, board_path, "whiteboard_svg")
            )
            board_ids.append(board_id)

        manifest: Dict[str, Any] = {
            "schema_version": body["schema_version"],
            "title": body["meta"]["title"],
            "theme": body.get("theme", "default"),
            "section_ids": [section["id"] for section in body["sections"]],
            "board_ids": board_ids,
            "asset_count": len(body.get("assets", [])),
            "artifacts": artifacts,
        }
        manifest_path = temporary_dir / "manifest.json"
        _write_text(
            manifest_path,
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )

        if output_dir.exists():
            shutil.rmtree(output_dir)
        temporary_dir.replace(output_dir)
        return manifest
    except Exception:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise
