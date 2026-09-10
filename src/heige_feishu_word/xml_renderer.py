"""Render a validated Body to supported Lark CLI Docx XML.

Native text stays searchable and editable. Sources stay beside the figures;
their complete editable data lives in an appendix to keep the reading flow clear.
"""
from __future__ import annotations
from html import escape
from typing import Any, Dict
from .model import validate_body
from .svg_renderer import render_workflow_svg
from .themes import get_theme

STATUS_LABELS = {"done": "已完成", "active": "进行中", "planned": "待开始", "risk": "有风险"}

def _e(value: Any) -> str:
    return escape(str(value), quote=False).replace("\n", "<br/>")

def _table(columns, rows, color='gray'):
    head = ''.join(f'<th background-color="light-{color}"><p><b><span text-color="{color}">{_e(c)}</span></b></p></th>' for c in columns)
    content = ''.join('<tr>'+''.join(f'<td vertical-align="top"><p>{_e(c)}</p></td>' for c in row)+'</tr>' for row in rows)
    return f'<table><thead><tr>{head}</tr></thead><tbody>{content}</tbody></table>'

def _grids(items, render, size=2):
    result = []
    for start in range(0, len(items), size):
        row = items[start:start+size]
        if len(row) == 1:
            result.append(render(row[0]))
            continue
        ratios = ['0.5', '0.5'] if len(row) == 2 else ['0.34', '0.33', '0.33']
        result.append('<grid>'+''.join(f'<column width-ratio="{ratios[i]}">{render(item)}</column>' for i,item in enumerate(row))+'</grid>')
    return ''.join(result)

def _render_section(section, theme, section_color=None):
    kind = section['type']
    color = section_color or theme['native']
    if kind == 'callout':
        tone = section.get('tone', 'info')
        hue, mark, label = {'info': (color, '💡', '要点'), 'success': ('green', '✅', '结论'),
                           'warning': ('orange', '❗', '关注'), 'risk': ('red', '⚠️', '风险')}[tone]
        return f'<callout emoji="{mark}" background-color="light-{hue}" border-color="{hue}"><p><b>{label}：</b>{_e(section["body"])}</p></callout>'
    if kind == 'prose':
        return ''.join(f'<p>{_e(p)}</p>' for p in section['paragraphs'])
    if kind == 'metrics':
        from .cover import render_metrics_svg_or_none
        svg = render_metrics_svg_or_none(section,theme)
        if svg is None:
            return _table(['指标','读数','口径与说明'], [[i['label'],i['value'],i['note']] for i in section['items']], color)
        return f'<whiteboard type="svg">{svg}</whiteboard>'
    if kind == 'grid':
        return _grids(section['items'], lambda item: f'<p><b><span text-color="{color}">{_e(item["title"])}</span></b></p><p>{_e(item["body"])}</p>', 2)
    if kind == 'table':
        return _table(section['columns'], section['rows'], color)
    if kind == 'comparison':
        return _table(['评估维度']+section['options'], [[r['label']]+r['values'] for r in section['criteria']], color)+f'<p><b>建议：</b>{_e(section["recommendation"])}</p>'
    if kind == 'timeline':
        hues = {'done':'green','active':'blue','planned':'gray','risk':'red'}
        return ''.join(f'<p><span background-color="light-{hues[i["status"]]}">{_e(i["date"])}</span>　<b>{_e(i["title"])}</b>（{STATUS_LABELS[i["status"]]}）</p><p>{_e(i["body"])}</p>' for i in section['items'])
    if kind == 'whiteboard_workflow':
        return f'<whiteboard type="svg">{render_workflow_svg(section, theme, embedded=True)}</whiteboard>'
    if kind == 'chart':
        from .charts import render_chart_svg
        return f'<p>{_e(section["insight"])}</p><whiteboard type="svg">{render_chart_svg(section, theme, embedded=True)}</whiteboard><p><span text-color="gray">数据来源：{_e(section["source"])}。本次输入快照，完整数据见文末明细。</span></p>'
    if kind == 'actions':
        return ''.join(f'<checkbox done="false"><b>{_e(i["owner"])}</b>｜{_e(i["action"])}｜{_e(i["due"])}</checkbox>' for i in section['items'])
    raise ValueError('unsupported section type: '+kind)

def _render_details(sections, theme):
    details = []
    for section in sections:
        kind = section['type']
        if kind == 'metrics':
            from .cover import render_metrics_svg_or_none
            if render_metrics_svg_or_none(section,theme) is None:
                continue
            content = _table(['指标','读数','口径与说明'], [[i['label'],i['value'],i['note']] for i in section['items']], theme['native'])
        elif kind == 'chart':
            from .charts import chart_table
            content = _table(*chart_table(section), color=theme['native'])
        elif kind == 'whiteboard_workflow':
            content = ''.join(f'<p><b>{n+1}．{_e(step["title"])}</b>　{_e(step["description"])}</p>' for n,step in enumerate(section['steps']))
        else:
            continue
        details.append(f'<p><b>{_e(section["title"])}</b></p>{content}')
    if not details:
        return ''
    return '<h1>数据与流程明细</h1><p><span text-color="gray">以下为图中内容的可编辑原始记录，便于查数、复制与核对。修改记录后请重新生成图形。</span></p>'+''.join(details)

def render_document_xml(body: Dict[str, Any]) -> str:
    validate_body(body)
    theme = get_theme(body.get('theme'))
    meta = body['meta']
    blocks = [f'<title>{_e(meta["title"])}</title>']
    if meta.get('subtitle'):
        blocks.append(f'<p>{_e(meta["subtitle"])}</p>')
    visible = [meta[k] for k in ('eyebrow','status','reading_time') if meta.get(k)]
    if visible:
        blocks.append(f'<p><span text-color="gray">{_e(" · ".join(visible))}</span></p>')
    if meta.get('audience'):
        blocks.append(f'<p><span text-color="gray">适用读者：{_e("、".join(meta["audience"]))}</span></p>')
    blocks.append('<hr/>')
    accents = theme['native_accents'][:2]
    for index, section in enumerate(body['sections']):
        color = accents[index % len(accents)]
        blocks.append(f'<h1 seq="auto"><span text-color="{color}">{_e(section["title"])}</span></h1>')
        blocks.append(_render_section(section, theme, color))
    details = _render_details(body['sections'], theme)
    if details:
        blocks.append(details)
    if meta.get('disclaimer'):
        blocks.append(f'<p><span text-color="gray">{_e(meta["disclaimer"])}</span></p>')
    return '\n'.join(blocks)+'\n'
