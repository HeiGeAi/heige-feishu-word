"""Render a validated Body to supported Lark CLI Docx XML.

Native text stays searchable and editable. Charts carry adjacent native data
and source paragraphs because the editable board is a snapshot of the input.
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

def _table(columns, rows):
    head = ''.join(f'<th background-color="light-gray"><p><b>{_e(c)}</b></p></th>' for c in columns)
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

def _render_section(section, theme):
    kind = section['type']
    color = theme['native']
    if kind == 'callout':
        tone = section.get('tone', 'info')
        hue, mark, label = {'info': (color, '💡', '要点'), 'success': ('green', '✅', '结论'),
                           'warning': ('orange', '❗', '关注'), 'risk': ('red', '⚠️', '风险')}[tone]
        return f'<callout emoji="{mark}" background-color="light-{hue}" border-color="{hue}"><p><b>{label}：</b>{_e(section["body"])}</p></callout>'
    if kind == 'prose':
        return ''.join(f'<p>{_e(p)}</p>' for p in section['paragraphs'])
    if kind == 'metrics':
        def metric(item):
            return f'<h2 seq="auto"><span text-color="{color}">{_e(item["value"])}</span></h2><p><b>{_e(item["label"])}</b></p><p><span text-color="gray">{_e(item["note"])}</span></p>'
        return _grids(section['items'], metric, 2)
    if kind == 'grid':
        return _grids(section['items'], lambda item: f'<h2 seq="auto">{_e(item["title"])}</h2><p>{_e(item["body"])}</p>', 2)
    if kind == 'table':
        return _table(section['columns'], section['rows'])
    if kind == 'comparison':
        return _table(['评估维度']+section['options'], [[r['label']]+r['values'] for r in section['criteria']])+f'<p><b>建议：</b>{_e(section["recommendation"])}</p>'
    if kind == 'timeline':
        return ''.join(f'<p><span background-color="light-{color}">{_e(i["date"])}</span>　<b>{_e(i["title"])}</b>（{STATUS_LABELS[i["status"]]}）</p><p>{_e(i["body"])}</p>' for i in section['items'])
    if kind == 'whiteboard_workflow':
        return f'<whiteboard type="svg">{render_workflow_svg(section, theme)}</whiteboard>' + ''.join(f'<p><b>{n+1}．{_e(step["title"])}</b>　{_e(step["description"])}</p>' for n,step in enumerate(section['steps']))
    if kind == 'chart':
        from .charts import render_chart_svg, chart_table
        columns, rows = chart_table(section)
        return f'<p><b>{_e(section["insight"])}</b></p><whiteboard type="svg">{render_chart_svg(section, theme)}</whiteboard>' + _table(columns, rows) + f'<p><span text-color="gray">数据来源：{_e(section["source"])}。图表为本次输入的静态快照。</span></p>'
    if kind == 'actions':
        return ''.join(f'<checkbox done="false"><b>{_e(i["owner"])}</b>｜{_e(i["action"])}｜{_e(i["due"])}</checkbox>' for i in section['items'])
    raise ValueError('unsupported section type: '+kind)

def render_document_xml(body: Dict[str, Any]) -> str:
    validate_body(body)
    theme = get_theme(body.get('theme'))
    meta = body['meta']
    blocks = [f'<title>{_e(meta["title"])}</title>']
    if meta.get('eyebrow'):
        blocks.append(f'<p><span text-color="{theme["native"]}"><b>{_e(meta["eyebrow"])}</b></span></p>')
    if meta.get('subtitle'):
        blocks.append(f'<p><b>{_e(meta["subtitle"])}</b></p>')
    visible = [meta[k] for k in ('status','reading_time') if meta.get(k)]
    if visible:
        blocks.append(f'<p><span text-color="gray">{_e(" · ".join(visible))}</span></p>')
    if meta.get('audience'):
        blocks.append(f'<p><span text-color="gray">适用读者：{_e("、".join(meta["audience"]))}</span></p>')
    if meta.get('eyebrow'):
        from .cover import render_cover_svg
        blocks.append(f'<whiteboard type="svg">{render_cover_svg(body, theme)}</whiteboard>')
    blocks.append('<hr/>')
    for section in body['sections']:
        blocks.append(f'<h1 seq="auto">{_e(section["title"])}</h1>')
        blocks.append(_render_section(section, theme))
    if meta.get('disclaimer'):
        blocks.append(f'<p><span text-color="gray">{_e(meta["disclaimer"])}</span></p>')
    return '\n'.join(blocks)+'\n'
