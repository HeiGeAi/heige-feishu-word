# Standard Sample Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish one test-first standard Feishu document sample from a reusable JSON Document Body.

**Architecture:** A Python 3.9 compatible, dependency-free compiler validates a section-based Body and generates Feishu XML, standalone SVG boards, and an artifact manifest. Network publication remains a separate, observable step using `lark-cli`, followed by readback and PDF QA.

**Tech Stack:** Python 3.9 standard library, `unittest`, `lark-cli 1.0.56`, `@larksuite/whiteboard-cli 0.2.12`, Poppler.

---

## File map

```text
pyproject.toml                         package metadata and CLI entry point
src/heige_feishu_word/model.py        Body loading and validation
src/heige_feishu_word/xml_renderer.py Feishu XML renderer
src/heige_feishu_word/svg_renderer.py safe workflow SVG renderer
src/heige_feishu_word/compiler.py     artifact bundle compiler
src/heige_feishu_word/cli.py          command line interface
tests/                                behavior-first unit tests
examples/standard-sample/body.json    approved synthetic business sample
scripts/publish_standard_sample.py    observable lark-cli orchestration
```

### Task 1: Establish the red test baseline

**Files:**

- Create: `pyproject.toml`
- Create: `tests/test_model.py`
- Create: `tests/test_xml_renderer.py`
- Create: `tests/test_svg_renderer.py`
- Create: `tests/test_compiler.py`

- [ ] **Step 1: Write failing behavior tests**

The tests import the wished-for API and assert these behaviors:

```python
from heige_feishu_word.model import BodyValidationError, validate_body

def test_rejects_unknown_section_type():
    body = minimal_body(section_type="unknown")
    with self.assertRaisesRegex(BodyValidationError, "unknown"):
        validate_body(body)
```

```python
from heige_feishu_word.xml_renderer import render_document_xml

def test_renders_semantic_blocks_and_embedded_whiteboard():
    xml = render_document_xml(valid_body())
    self.assertIn("<callout", xml)
    self.assertIn("<table>", xml)
    self.assertIn('<whiteboard type="svg">', xml)
    self.assertIn("统一 Document Body", xml)
```

```python
from heige_feishu_word.svg_renderer import render_workflow_svg, validate_svg

def test_workflow_svg_is_feishu_safe():
    svg = render_workflow_svg(workflow_section())
    report = validate_svg(svg)
    self.assertEqual(report.errors, ())
    self.assertIn('viewBox="0 0 1600 900"', svg)
```

```python
from heige_feishu_word.compiler import compile_body

def test_compile_writes_complete_artifact_bundle():
    manifest = compile_body(valid_body(), self.output_dir)
    self.assertEqual(manifest["schema_version"], "0.1")
    self.assertTrue((self.output_dir / "document.xml").is_file())
    self.assertTrue((self.output_dir / "boards" / "delivery-workflow.svg").is_file())
```

- [ ] **Step 2: Run tests and confirm expected RED state**

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Expected: imports fail because production modules do not exist yet.

- [ ] **Step 3: Commit the red baseline**

```bash
git add pyproject.toml tests
git commit -m "test: define standard sample contract"
```

### Task 2: Implement Body validation

**Files:**

- Create: `src/heige_feishu_word/__init__.py`
- Create: `src/heige_feishu_word/model.py`
- Test: `tests/test_model.py`

- [ ] **Step 1: Implement the minimal validator**

```python
SUPPORTED_SECTION_TYPES = {
    "callout", "metrics", "table", "grid", "whiteboard_workflow", "actions"
}

class BodyValidationError(ValueError):
    pass

def validate_body(body):
    if body.get("schema_version") != "0.1":
        raise BodyValidationError("schema_version must be 0.1")
    meta = body.get("meta")
    if not isinstance(meta, dict) or not str(meta.get("title", "")).strip():
        raise BodyValidationError("meta.title is required")
    sections = body.get("sections")
    if not isinstance(sections, list) or not sections:
        raise BodyValidationError("sections must be a non-empty list")
    seen = set()
    for section in sections:
        section_id = str(section.get("id", "")).strip()
        if not section_id or section_id in seen:
            raise BodyValidationError("section ids must be non-empty and unique")
        seen.add(section_id)
        section_type = section.get("type")
        if section_type not in SUPPORTED_SECTION_TYPES:
            raise BodyValidationError(f"unsupported section type: {section_type}")
    return body
```

- [ ] **Step 2: Run model tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_model -v
```

Expected: all model tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/heige_feishu_word tests/test_model.py
git commit -m "feat: validate document body"
```

### Task 3: Implement safe SVG workflow rendering

**Files:**

- Create: `src/heige_feishu_word/svg_renderer.py`
- Test: `tests/test_svg_renderer.py`

- [ ] **Step 1: Implement deterministic SVG rendering**

Use a fixed `1600 x 900` canvas, Raw Grid layout, real `<text>` nodes, and only `rect`, `circle`, `line`, `polyline`, `text`, `tspan`, `g`, and `svg` content elements. Escape every user string with `html.escape`.

```python
FORBIDDEN_TOKENS = (
    "<script", "<foreignObject", "<image", "<filter", "<mask",
    "<clipPath", "<linearGradient", "<radialGradient", " opacity=",
)

@dataclass(frozen=True)
class SvgValidationReport:
    errors: tuple
    warnings: tuple

def validate_svg(svg):
    errors = []
    if 'width="1600"' not in svg or 'height="900"' not in svg:
        errors.append("canvas must be 1600x900")
    if 'viewBox="0 0 1600 900"' not in svg:
        errors.append("viewBox must be 0 0 1600 900")
    lowered = svg.lower()
    for token in FORBIDDEN_TOKENS:
        if token.lower() in lowered:
            errors.append(f"forbidden SVG token: {token}")
    return SvgValidationReport(tuple(errors), ())
```

- [ ] **Step 2: Run SVG tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_svg_renderer -v
```

Expected: all SVG tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/heige_feishu_word/svg_renderer.py tests/test_svg_renderer.py
git commit -m "feat: render safe workflow boards"
```

### Task 4: Implement Feishu XML rendering

**Files:**

- Create: `src/heige_feishu_word/xml_renderer.py`
- Test: `tests/test_xml_renderer.py`

- [ ] **Step 1: Implement section renderers**

Render the six supported section types with a small dispatch table. Use Feishu semantic colors only and preserve the fixed rich-text nesting order.

```python
SECTION_RENDERERS = {
    "callout": _render_callout,
    "metrics": _render_metrics,
    "table": _render_table,
    "grid": _render_grid,
    "whiteboard_workflow": _render_workflow,
    "actions": _render_actions,
}

def render_document_xml(body):
    validate_body(body)
    meta = body["meta"]
    blocks = [f"<title>{escape(meta['title'])}</title>"]
    blocks.append(f"<h1>{escape(meta['title'])}</h1>")
    if meta.get("subtitle"):
        blocks.append(f"<p><b>{escape(meta['subtitle'])}</b></p>")
    for section in body["sections"]:
        blocks.append(SECTION_RENDERERS[section["type"]](section))
    return "\n".join(blocks) + "\n"
```

- [ ] **Step 2: Run XML tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_xml_renderer -v
```

Expected: all XML tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/heige_feishu_word/xml_renderer.py tests/test_xml_renderer.py
git commit -m "feat: render feishu document xml"
```

### Task 5: Compile the standard artifact bundle

**Files:**

- Create: `src/heige_feishu_word/compiler.py`
- Create: `src/heige_feishu_word/cli.py`
- Create: `src/heige_feishu_word/__main__.py`
- Create: `examples/standard-sample/body.json`
- Test: `tests/test_compiler.py`

- [ ] **Step 1: Implement bundle compilation**

`compile_body` must write atomically into a temporary sibling directory, then replace the destination only after all files validate. The manifest records SHA-256, byte size, section IDs and relative artifact paths.

```python
def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

- [ ] **Step 2: Run the full suite**

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Expected: all tests pass with zero failures.

- [ ] **Step 3: Compile the standard sample**

Run:

```bash
PYTHONPATH=src python3 -m heige_feishu_word compile \
  examples/standard-sample/body.json \
  --output build/standard-sample
```

Expected files:

```text
build/standard-sample/document.xml
build/standard-sample/source.body.json
build/standard-sample/manifest.json
build/standard-sample/boards/delivery-workflow.svg
```

- [ ] **Step 4: Render and inspect the board**

```bash
npx -y @larksuite/whiteboard-cli@0.2.12 \
  -i build/standard-sample/boards/delivery-workflow.svg \
  -o build/standard-sample/boards/delivery-workflow.png -f svg
npx -y @larksuite/whiteboard-cli@0.2.12 \
  -i build/standard-sample/boards/delivery-workflow.svg -f svg --check
```

Expected: PNG exists, CLI check returns exit code zero, and visual inspection finds no overlap or clipping.

- [ ] **Step 5: Commit**

```bash
git add src examples tests pyproject.toml
git commit -m "feat: compile standard sample bundle"
```

### Task 6: Publish, read back, export, and deliver

**Files:**

- Create: `scripts/publish_standard_sample.py`
- Create: `build/standard-sample/qa-report.json`

- [ ] **Step 1: Test command construction with a fake subprocess runner**

Assert that document creation uses stdin, all identities are explicit, local files are cwd-relative, and successful message results contain `message_id`.

- [ ] **Step 2: Run the full test suite before live writes**

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Expected: all tests pass with zero failures.

- [ ] **Step 3: Create and read back the Feishu document**

```bash
lark-cli docs +create --api-version v2 --as user --content - --json \
  < build/standard-sample/document.xml
lark-cli docs +fetch --api-version v2 --as user --doc "$DOC_TOKEN" \
  --detail with-ids --doc-format xml --json
```

Expected: creation returns `data.document.document_id`, `url`, and a whiteboard block token; readback contains all critical text anchors and a whiteboard token.

- [ ] **Step 4: Export and inspect the PDF**

```bash
lark-cli drive +export --as user --token "$DOC_TOKEN" --doc-type docx \
  --file-extension pdf --file-name standard-sample.pdf \
  --output-dir ./build/standard-sample/exports --overwrite --json
pdfinfo build/standard-sample/exports/standard-sample.pdf
pdftotext build/standard-sample/exports/standard-sample.pdf -
pdftoppm -png -r 150 build/standard-sample/exports/standard-sample.pdf \
  build/standard-sample/qa/page
```

Expected: the PDF opens, is non-empty, contains critical text anchors, and every page renders to PNG. Docx page count is reported as evidence rather than assumed to be exactly two.

- [ ] **Step 5: Send the completion notice and file body**

```bash
lark-cli im +messages-send --as bot --user-id "$USER_OPEN_ID" \
  --markdown "## heige-feishu-word 标准样本\n\n已生成：$DOC_URL" --json
cd build/standard-sample/exports
lark-cli im +messages-send --as bot --user-id "$USER_OPEN_ID" \
  --file ./standard-sample.pdf --json
```

Expected: both calls return a `message_id`.

- [ ] **Step 6: Pause for human visual approval**

Deliver only the cloud-document link, PDF, board preview, QA result and known limitations. Do not expand the template library or publish the public GitHub repository until the user approves the sample.

