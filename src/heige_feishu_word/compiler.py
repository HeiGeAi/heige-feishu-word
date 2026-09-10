"""Compile a Body into a deterministic, portable artifact bundle."""
from __future__ import annotations
import hashlib
import json
import shutil
import tempfile
import uuid
from pathlib import Path
from .model import BodyValidationError, validate_body
from .svg_renderer import render_workflow_svg, validate_svg
from .xml_renderer import render_document_xml
from .themes import get_theme


def sha256_file(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda:handle.read(65536),b''):
            digest.update(chunk)
    return digest.hexdigest()


def _write_text(path, content):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding='utf-8')


def _artifact_record(root,path,role):
    return dict(role=role,path=path.relative_to(root).as_posix(),bytes=path.stat().st_size,sha256=sha256_file(path))


def _check_destination(output_dir):
    if output_dir.is_symlink():
        raise BodyValidationError('output directory must not be a symlink')
    if output_dir.exists():
        if not output_dir.is_dir():
            raise BodyValidationError('output must be a directory')
        try:
            manifest=json.loads((output_dir/'manifest.json').read_text(encoding='utf-8'))
            records=manifest['artifacts']
            for record in records:
                relative=Path(record['path'])
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('invalid artifact path')
            expected={r['path'] for r in records}|{'manifest.json'}
            actual={p.relative_to(output_dir).as_posix() for p in output_dir.rglob('*') if p.is_file()}
            intact=all(sha256_file(output_dir/r['path'])==r['sha256'] for r in records)
            if actual!=expected or not intact or not records or any(p.is_symlink() for p in output_dir.rglob('*')):
                raise ValueError('modified output')
        except (OSError,ValueError,KeyError,TypeError) as exc:
            raise BodyValidationError('output contains untracked or modified files; choose a new directory') from exc


def compile_body(body, output_dir):
    validate_body(body)
    if body.get('assets'):
        raise BodyValidationError('compiler does not ingest assets yet; no asset was dropped')
    theme=get_theme(body.get('theme'))
    output_dir=Path(output_dir).absolute()
    _check_destination(output_dir)
    output_dir.parent.mkdir(parents=True,exist_ok=True)
    temporary_dir=Path(tempfile.mkdtemp(prefix=f'.{output_dir.name}.',dir=str(output_dir.parent)))
    backup=None
    try:
        artifacts=[]
        def write(relative,content,role):
            target=temporary_dir/relative
            _write_text(target,content)
            artifacts.append(_artifact_record(temporary_dir,target,role))
        write('source.body.json',json.dumps(body,ensure_ascii=False,indent=2,sort_keys=True)+'\n','source_body')
        xml=render_document_xml(body)
        write('document.xml',xml,'feishu_xml')
        from .preview import render_preview_html,render_overview_html
        write('preview.html',render_preview_html(body),'local_preview')
        write('theme.json',json.dumps(theme,ensure_ascii=False,indent=2,sort_keys=True)+'\n','theme_tokens')
        board_ids=[]
        def board(board_id,svg):
            report=validate_svg(svg)
            if report.errors:
                raise BodyValidationError(f'invalid SVG for {board_id}: '+ '; '.join(report.errors))
            write(f'boards/{board_id}.svg',svg+'\n','whiteboard_svg')
            board_ids.append(board_id)
        from .cover import render_metrics_svg_or_none
        metrics=next((s for s in body['sections'] if s['type']=='metrics'),None)
        cover=render_metrics_svg_or_none(metrics,theme) if metrics else None
        if cover is not None:
            overview=render_overview_html(body)
            if len(overview.encode('utf-8'))>500_000:
                raise BodyValidationError('HTML overview exceeds the 500KB Lark block limit')
            write('widgets/overview.html',overview,'html_overview')
            enhanced=xml.replace(f'<whiteboard type="svg">{cover}</whiteboard>', '<html5-block path="@./widgets/overview.html"/>',1)
            write('document.enhanced.xml',enhanced,'feishu_xml_optional_html')
        for section in body['sections']:
            if section['type']=='metrics':
                metric_svg=render_metrics_svg_or_none(section,theme)
                if metric_svg is not None:
                    board(section['id'],metric_svg)
            elif section['type']=='whiteboard_workflow':
                board(section['id'],render_workflow_svg(section,theme,embedded=True))
            elif section['type']=='chart':
                from .charts import render_chart_svg
                board(section['id'],render_chart_svg(section,theme,embedded=True))
                write(f'standalone/{section["id"]}.svg',render_chart_svg(section,theme)+'\n','standalone_chart_svg')
        manifest=dict(schema_version=body['schema_version'],generator='heige-feishu-word',
            title=body['meta']['title'],theme=theme['slug'],section_ids=[s['id'] for s in body['sections']],
            board_ids=board_ids,asset_count=0,artifacts=artifacts,
            capabilities={'charts':'static snapshots with native data tables','cloud_status':'not_published',
                          'preview':'local design preview; native Docx uses client fonts and colors',
                          'enhanced':'optional HTML overview; client support requires verification'})
        _write_text(temporary_dir/'manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
        _check_destination(output_dir)
        if output_dir.exists():
            backup=output_dir.with_name(f'.{output_dir.name}.backup-{uuid.uuid4().hex}')
            output_dir.replace(backup)
        try:
            if backup:
                _check_destination(backup)
            temporary_dir.replace(output_dir)
        except Exception:
            if backup:
                backup.replace(output_dir)
                backup=None
            raise
        if backup:
            shutil.rmtree(backup)
        return manifest
    finally:
        if temporary_dir.exists():
            shutil.rmtree(temporary_dir)
