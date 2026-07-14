"""Command line entry point for local Body validation and compilation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Sequence

from .compiler import compile_body
from .model import BodyValidationError, validate_body


def _load_body(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BodyValidationError("body JSON must contain an object")
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="heige-feishu-word",
        description="Compile a structured Body into Feishu delivery artifacts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate a Body JSON")
    validate_parser.add_argument("body", type=Path)

    compile_parser = subparsers.add_parser("compile", help="compile a Body JSON")
    compile_parser.add_argument("body", type=Path)
    compile_parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI and return a process-style exit code."""

    args = _parser().parse_args(argv)
    try:
        body = _load_body(args.body)
        validate_body(body)
        if args.command == "validate":
            result = {"ok": True, "title": body["meta"]["title"]}
        else:
            manifest = compile_body(body, args.output)
            result = {
                "ok": True,
                "output": str(args.output.resolve()),
                "manifest": manifest,
            }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (BodyValidationError, OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"ok": False, "error": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

