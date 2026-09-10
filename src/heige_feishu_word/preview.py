"""White-page document previews and compact, static Feishu metric blocks.

The preview follows a document column rather than an independent website.
User content is escaped; all fonts and assets remain local to the output.
"""

from __future__ import annotations

from html import escape
import re
from typing import Any, Dict, Iterable

from .model import validate_body
from .themes import get_theme


_STATUS = {"done": "已完成", "active": "进行中", "planned": "待开始", "risk": "有风险"}
_TONE = {"success": "结论", "warning": "关注", "risk": "风险", "info": "要点"}
_SANS = '"Inter","Helvetica Neue","Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif'
_SERIF = 'Georgia,"Noto Serif SC","Songti SC","STSong",serif'
_MONO = '"IBM Plex Mono","SFMono-Regular",Menlo,"Noto Sans SC","PingFang SC",monospace'


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


def _text(value: Any) -> str:
    return _e(value).replace("\n", "<br>")


def _tokens(theme: dict) -> str:
    # Only trusted registry tokens may become CSS values.
    return ":root{" + ";".join(
        "--" + key + ":" + theme[key]
        for key in ("canvas", "surface", "ink", "muted", "hairline", "primary", "secondary")
    ) + ";--sans:" + _SANS + ";--serif:" + _SERIF + ";--mono:" + _MONO + ";}"


_CSS = r"""
*{box-sizing:border-box}
html{scroll-behavior:smooth;background:#fff}
body{margin:0;background:#fff;color:var(--ink);font:16px/1.75 var(--sans);overflow-wrap:anywhere}
p,h1,h2,h3,figure{margin:0}p+p{margin-top:12px}
h1,h2,h3{overflow-wrap:anywhere;text-wrap:pretty}
h1{font-size:32px;line-height:1.4;letter-spacing:-.025em;font-weight:650}
h2{font-size:21px;line-height:1.5;font-weight:650}
h3{font-size:16px;line-height:1.65;font-weight:650}
a{color:inherit;text-underline-offset:3px}button{font:inherit;color:inherit}
button,summary{cursor:pointer}button,a,summary{-webkit-tap-highlight-color:transparent}
button:focus-visible,a:focus-visible,summary:focus-visible,[tabindex]:focus-visible{outline:2px solid var(--primary);outline-offset:4px}
svg{display:block;max-width:100%;height:auto}
.document-main,.toolbar-inner{width:min(820px,calc(100% - 64px));margin-inline:auto;min-width:0}
.toolbar{border-bottom:1px solid #edf0f3}
.toolbar-inner{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:10px 0;color:var(--muted);font-size:12px}
.toolbar-label{overflow-wrap:anywhere}.quiet-button{padding:5px 10px;border:1px solid var(--hairline);border-radius:3px;background:#fff;font-size:12px;line-height:1.5;white-space:nowrap}
.quiet-button:hover{background:#f7f8fa}.document-header{padding:28px 0 20px;border-bottom:1px solid var(--hairline)}
.eyebrow{display:flex;align-items:center;gap:8px;font-size:12px;line-height:1.5;color:var(--muted);margin-bottom:10px}
.document-mark{display:block;width:20px;height:2px;flex-shrink:0;background:var(--primary);transform-origin:left;animation:mark-arrive .22s ease-out both}
.subtitle{margin-top:10px;color:var(--muted);font-size:14px;line-height:1.7}
.meta{display:flex;flex-wrap:wrap;gap:4px 16px;color:var(--muted);font-size:12px;line-height:1.65;margin-top:9px}
.meta .audience{flex-basis:100%}.doc-section{margin-top:28px;min-width:0;scroll-margin-top:20px}
.section-heading{display:flex;align-items:baseline;gap:10px;margin-bottom:12px}
.section-no{font:11px/1.5 var(--mono);color:var(--muted);flex-shrink:0}
.section-content{min-width:0}.callout{border-left:3px solid var(--primary);padding:12px 16px;background:#f7f8fa;border-radius:0 3px 3px 0}
.callout-label{font-size:11px;font-weight:650;color:var(--muted);margin-bottom:4px}.callout p{font-size:16px;line-height:1.75}
.callout[data-tone="warning"],.callout[data-tone="risk"]{border-left-style:double;border-left-width:4px}
.table-scroll{overflow-x:auto;max-width:100%;border:1px solid var(--hairline);border-radius:3px}
table{width:100%;border-collapse:collapse;text-align:left;font-size:14px;line-height:1.65}
th,td{padding:10px 12px;border-bottom:1px solid var(--hairline);vertical-align:top;min-width:104px}
th{font-weight:600;background:#f7f8fa}tr:last-child td{border-bottom:0}td:first-child{font-weight:500}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 28px}
.grid-item{padding-top:10px;border-top:1px solid var(--hairline)}.grid-item p{font-size:14px;line-height:1.8;margin-top:5px}
.actions{list-style:none;margin:0;padding:0}.action{display:grid;grid-template-columns:15px minmax(0,1fr);gap:10px;padding:11px 0;border-top:1px solid var(--hairline)}
.action-box{width:13px;height:13px;border:1px solid var(--muted);border-radius:2px;margin-top:7px}.action-task{font-size:15px}
.action-meta{display:flex;gap:4px 16px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:3px}
.timeline{list-style:none;padding:0;margin:0}.milestone{display:grid;grid-template-columns:84px 16px minmax(0,1fr);gap:12px;position:relative;padding-bottom:22px}
.milestone:last-child{padding-bottom:0}.milestone-date{font-size:12px;line-height:1.65;color:var(--muted);padding-top:3px}
.milestone-marker{position:relative;display:flex;justify-content:center}.milestone-marker:after{content:"";position:absolute;top:14px;bottom:-23px;left:8px;width:1px;background:var(--hairline)}
.milestone:last-child .milestone-marker:after{display:none}.milestone-dot{height:8px;width:8px;border:1.5px solid var(--muted);background:#fff;border-radius:50%;margin-top:8px;position:relative;z-index:1}
.milestone[data-status="done"] .milestone-dot,.milestone[data-status="active"] .milestone-dot{background:var(--primary);border-color:var(--primary)}
.milestone[data-status="risk"] .milestone-dot{border-radius:0;transform:rotate(45deg)}.milestone-header{display:flex;align-items:baseline;gap:12px}
.milestone-status{font-size:11px;color:var(--muted);white-space:nowrap}.milestone p{margin-top:4px;font-size:14px}
.recommendation{margin-top:12px;border-left:2px solid var(--primary);padding-left:12px;font-size:15px}
.chart-insight{font-size:16px;line-height:1.75;margin-bottom:12px}.diagram-scroll{width:100%;max-width:100%;overflow:auto;background:#fff}
.diagram-open{display:block;width:100%;border:0;background:#fff;padding:0;text-align:left;transition:opacity .15s ease-out}
.diagram-open:hover{opacity:.9}.diagram-open svg{width:100%;max-width:none;height:auto}
.figure-caption{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-top:6px;font-size:12px;line-height:1.7;color:var(--muted)}
.figure-caption span{min-width:0}.figure-hint{flex-shrink:0;font-size:11px;white-space:nowrap}.phone-hint{display:none}
details{margin-top:9px}summary{width:fit-content;max-width:100%;padding:3px 0;font-size:12px;color:var(--muted)}details[open] summary{margin-bottom:8px}
.workflow-list{padding-left:1.5em;font-size:14px;margin:0}.workflow-list li{padding:5px 0}.workflow-list strong{margin-right:8px}
.document-footer{margin-top:36px;padding:16px 0 36px;border-top:1px solid var(--hairline);font-size:12px;line-height:1.8;color:var(--muted)}
.figure-dialog{width:min(1280px,94vw);max-width:94vw;max-height:92vh;border:1px solid var(--hairline);border-radius:4px;background:#fff;color:var(--ink);padding:0}
.figure-dialog::backdrop{background:rgba(17,24,39,.58)}.dialog-controls{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:12px 16px;border-bottom:1px solid var(--hairline)}
.dialog-controls strong{font-size:14px}.dialog-buttons{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.dialog-scroll{overflow:auto;max-height:76vh;padding:12px}
.dialog-art{width:100%;max-width:none;transform-origin:top left}.dialog-art svg{width:100%;max-width:none;height:auto}
/* Small document marks survive the shared white sheet. */
body[data-layout="editorial"] .document-header h1{font-family:var(--serif);font-weight:600}
body[data-layout="editorial"] .document-mark{width:28px;height:1px}
body[data-layout="ledger"] .section-no{color:var(--primary)}body[data-layout="ledger"] .section-no:before{content:"§"}
body[data-layout="ledger"] .document-mark{width:8px;height:8px}body[data-layout="ledger"] table{font-variant-numeric:tabular-nums}
body[data-layout="nocturne"] .document-mark{width:6px;height:6px;border-radius:50%}
body[data-layout="nocturne"] .milestone-status{font-variant-numeric:tabular-nums}
body[data-layout="press"] .document-header{border-bottom:3px double var(--hairline)}body[data-layout="press"] .document-header h1{font-family:var(--serif);font-weight:700}
body[data-layout="press"] .document-mark{height:4px;background:transparent;border-block:1px solid var(--primary)}
body[data-layout="ink"] .document-header h1{font-family:var(--serif);font-weight:600}
body[data-layout="ink"] .document-mark{width:9px;height:9px;background:transparent;border:2px solid var(--primary)}
body[data-layout="festival"] .document-mark{width:22px;height:3px}
body[data-layout="festival"] .section-heading h2{font-weight:700}
@keyframes mark-arrive{from{opacity:0;transform:scaleX(.6)}to{opacity:1;transform:scaleX(1)}}
@media(max-width:600px){
.document-main,.toolbar-inner{width:calc(100% - 32px)}.toolbar-inner{font-size:11px;gap:10px}.document-header{padding:22px 0 16px}
h1{font-size:28px;line-height:1.45}h2{font-size:20px}.subtitle{font-size:13px}.meta{gap:4px 12px;font-size:11px}.doc-section{margin-top:24px}
.grid{grid-template-columns:1fr;gap:16px}.section-heading{gap:8px}.callout{padding:10px 12px}.callout p{font-size:15px}
.figure-caption{display:block}.figure-hint{display:block;margin-top:4px}.phone-hint{display:inline}.diagram-open{min-width:640px}.dialog-controls{align-items:flex-start;flex-direction:column;padding:12px;gap:8px}
.dialog-buttons{width:100%}.dialog-buttons .quiet-button{padding:5px 8px}.dialog-scroll{padding:8px}
.milestone{grid-template-columns:68px 12px minmax(0,1fr);gap:8px}.milestone-marker:after{left:6px}.milestone-header{flex-wrap:wrap;gap:0 8px}
.document-footer{margin-top:28px;padding-bottom:28px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{animation:none!important;transition:none!important}}
@media print{.toolbar,.figure-hint,.figure-dialog{display:none!important}body{background:#fff;color:#111;font-size:11pt}.document-main{width:100%}.document-header{padding-top:0}.doc-section{margin-top:22px;break-inside:avoid-page}h1{font-size:24pt}h2{font-size:15pt}.diagram-open{min-width:0}.diagram-scroll,.table-scroll{overflow:visible}.figure-caption{font-size:9pt}details:not([open])>*:not(summary){display:revert}summary{display:none}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


_OVERVIEW_CSS = r"""
*{box-sizing:border-box}html,body{margin:0;background:#fff;color:var(--ink);font:14px/1.65 var(--sans);overflow-wrap:anywhere}
.metric-overview{width:100%;padding:4px 0}.overview-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;border-top:1px solid var(--hairline);border-bottom:1px solid var(--hairline)}
.overview-metric{padding:16px 18px;min-width:0}.overview-metric+.overview-metric{border-left:1px solid var(--hairline)}
.overview-value{margin:0;font-size:28px;line-height:1.3;font-weight:650;font-variant-numeric:tabular-nums;letter-spacing:-.02em}.overview-metric:first-child .overview-value{color:var(--primary)}
.overview-label{margin:7px 0 0;font-size:13px;font-weight:600}.overview-note{margin:5px 0 0;font-size:11px;line-height:1.7;color:var(--muted)}
body[data-layout="ledger"] .overview-value,body[data-layout="nocturne"] .overview-value{font-family:var(--mono)}
body[data-layout="editorial"] .overview-value,body[data-layout="ink"] .overview-value{font-family:var(--serif)}
@media(max-width:640px){.overview-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.overview-metric{padding:13px 12px}.overview-metric:nth-child(2n+1){border-left:0}.overview-metric:nth-child(n+3){border-top:1px solid var(--hairline)}.overview-value{font-size:25px}}
@media(max-width:280px){.overview-metrics{grid-template-columns:1fr}.overview-metric+.overview-metric{border-left:0;border-top:1px solid var(--hairline)}}
@media print{*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


_JS = r"""
(()=>{'use strict';
const printButton=document.querySelector('[data-print]');
if(printButton)printButton.addEventListener('click',()=>window.print());
let openedForPrint=[];
window.addEventListener('beforeprint',()=>{openedForPrint=Array.from(document.querySelectorAll('details:not([open])'));openedForPrint.forEach(item=>{item.open=true;});});
window.addEventListener('afterprint',()=>{openedForPrint.forEach(item=>{item.open=false;});openedForPrint=[];});
const dialog=document.getElementById('figure-dialog');if(!dialog)return;
const art=dialog.querySelector('.dialog-art');const scroll=dialog.querySelector('.dialog-scroll');
const label=dialog.querySelector('#figure-dialog-title');
let nativeWidth=1600;let currentWidth=1600;let origin=null;let serial=0;
const resize=width=>{currentWidth=width;art.style.width=width+'px';};
const close=()=>{if(typeof dialog.close==='function')dialog.close();else dialog.removeAttribute('open');if(origin)origin.focus();};
const fit=()=>{const style=getComputedStyle(scroll);resize(Math.max(1,scroll.clientWidth-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight)));scroll.scrollTo(0,0);};
document.querySelectorAll('.diagram-open').forEach(button=>{button.addEventListener('click',()=>{
const original=button.querySelector('svg');if(!original)return;origin=button;
const copy=original.cloneNode(true);serial+=1;
// Clone only generated SVGs and remap identifiers to avoid fragment collisions.
const nodes=[copy,...copy.querySelectorAll('*')];const remap=new Map();
nodes.forEach(node=>{if(node.id){const old=node.id;const next='zoom-'+serial+'-'+old;remap.set(old,next);node.id=next;}});
nodes.forEach(node=>Array.from(node.attributes).forEach(attr=>{let value=attr.value;remap.forEach((next,old)=>{value=value.split('url(#'+old+')').join('url(#'+next+')');if(value==='#'+old)value='#'+next;});if(value!==attr.value)node.setAttribute(attr.name,value);}));
art.replaceChildren(copy);label.textContent=button.dataset.title;
const viewBox=original.viewBox&&original.viewBox.baseVal;nativeWidth=(viewBox&&viewBox.width)||parseFloat(original.getAttribute('width'))||1600;
if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','');
resize(nativeWidth);scroll.scrollTo(0,0);
});});
dialog.querySelector('[data-close]').addEventListener('click',close);
dialog.querySelector('[data-enlarge]').addEventListener('click',()=>resize(Math.min(nativeWidth*3,currentWidth*1.25)));
dialog.querySelector('[data-actual]').addEventListener('click',()=>{resize(nativeWidth);scroll.scrollTo(0,0);});
dialog.querySelector('[data-fit]').addEventListener('click',fit);
dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&dialog.hasAttribute('open')){event.preventDefault();close();}});
dialog.addEventListener('click',event=>{if(event.target===dialog){const box=dialog.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)close();}});
})();
"""


def _header(meta: dict, theme: dict) -> str:
    eyebrow = '<p class="eyebrow"><span class="document-mark" aria-hidden="true"></span>' + _text(meta.get("eyebrow", theme["name"])) + "</p>"
    subtitle = '<p class="subtitle">' + _text(meta["subtitle"]) + "</p>" if meta.get("subtitle") else ""
    metadata = ["<span>" + _text(meta[key]) + "</span>" for key in ("status", "reading_time") if meta.get(key)]
    if meta.get("audience"):
        metadata.append('<span class="audience">适用读者：' + _text("、".join(meta["audience"])) + "</span>")
    return '<header class="document-header">' + eyebrow + "<h1>" + _text(meta["title"]) + "</h1>" + subtitle + '<div class="meta">' + "".join(metadata) + "</div></header>"


def _table(columns: list, rows: list, label: str) -> str:
    head = "".join('<th scope="col">' + _text(value) + "</th>" for value in columns)
    body = "".join("<tr>" + "".join("<td>" + _text(value) + "</td>" for value in row) + "</tr>" for row in rows)
    return '<div class="table-scroll" tabindex="0" role="region" aria-label="' + _e(label) + '"><table><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table></div>"


def _figure(svg: str, title: str, caption: str = "") -> str:
    caption_text = "<span>" + _text(caption) + "</span>" if caption else "<span></span>"
    return '<figure><div class="diagram-scroll" tabindex="0" role="region" aria-label="' + _e(title + "，窄屏可横向滑动") + '"><button class="diagram-open" type="button" data-title="' + _e(title) + '" aria-label="' + _e("查看大图：" + title) + '">' + svg + '</button></div><figcaption class="figure-caption">' + caption_text + '<span class="figure-hint"><span class="phone-hint">窄屏可横向滑动，</span>点击查看原尺寸</span></figcaption></figure>'


def _section_content(section: dict, theme: dict) -> str:
    kind = section["type"]
    if kind == "prose":
        return '<div class="prose">' + "".join("<p>" + _text(p) + "</p>" for p in section["paragraphs"]) + "</div>"
    if kind == "callout":
        tone = section.get("tone", "info")
        return '<aside class="callout" data-tone="' + _e(tone) + '"><div class="callout-label">' + _TONE[tone] + "</div><p>" + _text(section["body"]) + "</p></aside>"
    if kind == "metrics":
        from .cover import render_metrics_svg_or_none
        rows = [[item["label"], item["value"], item["note"]] for item in section["items"]]
        svg = render_metrics_svg_or_none(section, theme)
        table = _table(["指标", "数值", "说明"], rows, section["title"] + "指标表")
        if svg is None:
            return table
        return _figure(svg, section["title"]) + '<details><summary>查看指标文字与口径</summary>' + table + "</details>"
    if kind == "table":
        return _table(section["columns"], section["rows"], section["title"])
    if kind == "grid":
        return '<div class="grid">' + "".join('<article class="grid-item"><h3>' + _text(item["title"]) + "</h3><p>" + _text(item["body"]) + "</p></article>" for item in section["items"]) + "</div>"
    if kind == "actions":
        return '<ol class="actions">' + "".join('<li class="action"><span class="action-box" aria-hidden="true"></span><div><p class="action-task">' + _text(item["action"]) + '</p><p class="action-meta"><span>负责人：' + _text(item["owner"]) + "</span><span>截止：" + _text(item["due"]) + "</span></p></div></li>" for item in section["items"]) + "</ol>"
    if kind == "timeline":
        return '<ol class="timeline">' + "".join('<li class="milestone" data-status="' + _e(item["status"]) + '"><time class="milestone-date">' + _text(item["date"]) + '</time><div class="milestone-marker" aria-hidden="true"><span class="milestone-dot"></span></div><div class="milestone-content"><div class="milestone-header"><h3>' + _text(item["title"]) + '</h3><span class="milestone-status">' + _STATUS[item["status"]] + "</span></div><p>" + _text(item["body"]) + "</p></div></li>" for item in section["items"]) + "</ol>"
    if kind == "comparison":
        return _table(["评估维度"] + section["options"], [[row["label"]] + row["values"] for row in section["criteria"]], section["title"]) + '<p class="recommendation"><strong>建议：</strong>' + _text(section["recommendation"]) + "</p>"
    if kind == "whiteboard_workflow":
        from .svg_renderer import render_workflow_svg
        steps = "".join("<li><strong>" + _text(step["title"]) + "</strong>" + _text(step["description"]) + "</li>" for step in section["steps"])
        return _figure(render_workflow_svg(section, theme, embedded=True), section["title"]) + '<details><summary>查看流程文字</summary><ol class="workflow-list">' + steps + "</ol></details>"
    if kind == "chart":
        from .charts import chart_table, render_chart_svg
        columns, rows = chart_table(section)
        caption = "数据来源：" + section["source"] + "。本次输入的静态快照。"
        if section.get("unit"):
            caption = "单位：" + section["unit"] + "。" + caption
        return '<p class="chart-insight">' + _text(section["insight"]) + "</p>" + _figure(render_chart_svg(section, theme, embedded=True), section["title"], caption) + '<details><summary>查看完整数据表</summary>' + _table(columns, rows, section["title"] + "数据表") + "</details>"
    raise ValueError("unsupported preview section type: " + kind)


def _section(section: dict, theme: dict, index: int) -> str:
    return '<section class="doc-section" id="section-' + _e(section["id"]) + '" data-section-type="' + _e(section["type"]) + '"><div class="section-heading"><span class="section-no">' + f'{index:02d}' + "</span><h2>" + _text(section["title"]) + '</h2></div><div class="section-content">' + _section_content(section, theme) + "</div></section>"


def _document(title: str, theme: dict, content: str, overview: bool = False, extra_css: str = "", script: str = "") -> str:
    metas = '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
    if overview:
        metas += '<meta name="use-iframe" content="true"><meta name="html-box-height-mode" content="auto">'
    css = _OVERVIEW_CSS if overview else _CSS
    return '<!doctype html><html lang="zh-CN"><head>' + metas + "<title>" + _e(title) + "</title><style>" + _tokens(theme) + css + extra_css + '</style></head><body data-theme="' + theme["slug"] + '" data-layout="' + theme["layout"] + '"' + (' class="overview"' if overview else "") + ">" + content + ("<script>" + script + "</script>" if script else "") + "</body></html>\n"


def render_preview_html(body: Dict[str, Any]) -> str:
    """Render complete content in a white 820 px document column."""
    validate_body(body)
    theme = get_theme(body.get("theme"))
    meta = body["meta"]
    toolbar = '<div class="toolbar"><div class="toolbar-inner"><span class="toolbar-label">白页文档预览 · 飞书原生排版以客户端为准</span><button class="quiet-button" type="button" data-print>打印</button></div></div>'
    content = toolbar + '<main class="document-main">' + _header(meta, theme)
    content += "".join(_section(section, theme, i + 1) for i, section in enumerate(body["sections"]))
    if meta.get("disclaimer"):
        content += '<footer class="document-footer"><p>' + _text(meta["disclaimer"]) + "</p></footer>"
    content += "</main>"
    content += '<dialog class="figure-dialog" id="figure-dialog" aria-labelledby="figure-dialog-title"><div class="dialog-controls"><strong id="figure-dialog-title">图表大图</strong><div class="dialog-buttons"><button type="button" class="quiet-button" data-actual>原尺寸</button><button type="button" class="quiet-button" data-enlarge aria-label="放大图表">放大</button><button type="button" class="quiet-button" data-fit>适应宽度</button><button type="button" class="quiet-button" data-close autofocus>关闭</button></div></div><div class="dialog-scroll" tabindex="0" role="region" aria-label="图表大图，可滚动查看"><div class="dialog-art"></div></div></dialog>'
    return _document(meta["title"], theme, content, script=_JS)


def render_overview_html(body: Dict[str, Any]) -> str:
    """Render only the first metric group for an optional static html5-block.

    The surrounding native document already owns its title, metadata, section
    heading and disclaimer. The widget must not repeat any of those elements.
    """
    validate_body(body)
    theme = get_theme(body.get("theme"))
    metrics = next((section for section in body["sections"] if section["type"] == "metrics"), None)
    content = '<main class="metric-overview">'
    if metrics:
        content += '<div class="overview-metrics">' + "".join(
            '<article class="overview-metric"><p class="overview-value">' + _text(item["value"]) +
            '</p><p class="overview-label">' + _text(item["label"]) +
            '</p><p class="overview-note">' + _text(item["note"]) + "</p></article>"
            for item in metrics["items"]
        ) + "</div>"
    content += "</main>"
    result = _document("指标速览", theme, content, overview=True)
    if len(result.encode("utf-8")) > 500_000:
        raise ValueError("HTML overview exceeds the 500 KB Feishu content limit")
    return result


_GALLERY_CSS = r"""
.gallery-main{width:min(820px,calc(100% - 64px));margin:0 auto;padding-top:24px}
.gallery-masthead{display:flex;align-items:center;justify-content:space-between;gap:16px;font:11px/1.6 var(--mono);color:var(--muted);padding-bottom:14px;border-bottom:1px solid var(--hairline)}
.gallery-intro{padding:28px 0 26px}.gallery-intro h1{font-size:32px;line-height:1.45}.gallery-intro p{font-size:15px;line-height:1.8;color:var(--muted);margin-top:12px;max-width:46em}
.gallery-list{list-style:none;padding:0;margin:0}.gallery-entry{display:grid;grid-template-columns:24px minmax(0,1fr) 184px 18px;gap:18px;align-items:center;border-top:1px solid var(--hairline);padding:22px 0;text-decoration:none}
.gallery-entry:hover h2{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:4px}.gallery-entry:hover .gallery-arrow{transform:translateX(3px)}
.gallery-number{align-self:start;font:11px/1.6 var(--mono);color:var(--muted);padding-top:5px}.gallery-copy h2{font-size:20px;line-height:1.5}.gallery-copy p{font-size:13px;line-height:1.75;color:var(--muted);margin-top:7px}
.gallery-slug{display:block;font-size:11px;color:var(--muted);margin-top:8px}.gallery-arrow{font-size:18px;transition:transform .16s ease-out}
.gallery-swatch{min-width:0;height:110px;background:#fff;border:1px solid var(--swatch-hairline);padding:13px;color:var(--swatch-ink);display:flex;flex-direction:column;justify-content:space-between}
.swatch-line{width:20px;height:2px;background:var(--swatch-primary)}.swatch-title{font-size:12px;font-weight:600;line-height:1.5}.swatch-bars{display:flex;gap:5px;align-items:end;height:19px;border-bottom:1px solid var(--swatch-hairline)}
.swatch-bars i{height:100%;width:14px;background:var(--swatch-primary)}.swatch-bars i:nth-child(2){height:65%;background:var(--swatch-hairline)}.swatch-bars i:nth-child(3){height:42%;background:var(--swatch-hairline)}
.gallery-swatch[data-preview-layout="editorial"] .swatch-title,.gallery-swatch[data-preview-layout="ink"] .swatch-title{font-family:var(--serif)}
.gallery-swatch[data-preview-layout="ledger"] .swatch-line{width:6px;height:6px}.gallery-swatch[data-preview-layout="nocturne"] .swatch-line{width:6px;height:6px;border-radius:50%}
.gallery-swatch[data-preview-layout="press"]{border-top:3px double var(--swatch-hairline)}.gallery-swatch[data-preview-layout="ink"] .swatch-line{width:8px;height:8px;border:1px solid var(--swatch-primary);background:#fff}
.gallery-swatch[data-preview-layout="festival"] .swatch-line{width:26px;height:3px}
.gallery-footer{padding:18px 0 32px;border-top:1px solid var(--hairline);font-size:12px;line-height:1.8;color:var(--muted)}
@media(max-width:600px){.gallery-main{width:calc(100% - 32px);padding-top:16px}.gallery-masthead{font-size:10px}.gallery-intro{padding:22px 0}.gallery-intro h1{font-size:28px}.gallery-entry{grid-template-columns:20px minmax(0,1fr) 18px;gap:12px;padding:19px 0}.gallery-copy h2{font-size:19px}.gallery-swatch{display:none}.gallery-intro p{font-size:14px}}
"""


def render_gallery_html(entries: Iterable[Dict[str, Any]]) -> str:
    """Render a local white-page sample directory with restrained theme marks."""
    entries = list(entries)
    parts = []
    for index, entry in enumerate(entries, 1):
        slug = str(entry["slug"])
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", slug):
            raise ValueError("gallery slug must be a safe local directory name")
        supplied_theme = entry.get("theme", slug)
        theme = get_theme(supplied_theme.get("slug") if isinstance(supplied_theme, dict) else supplied_theme)
        colors = ";".join("--swatch-" + key + ":" + theme[key] for key in ("ink", "primary", "hairline"))
        swatch = '<div class="gallery-swatch" aria-hidden="true" data-preview-layout="' + theme["layout"] + '" style="' + colors + '"><span class="swatch-line"></span><span class="swatch-title">' + _e(theme["name"]) + '</span><span class="swatch-bars"><i></i><i></i><i></i></span></div>'
        parts.append('<li><a class="gallery-entry" href="' + _e(slug) + '/preview.html"><span class="gallery-number">' + f'{index:02d}' + '</span><div class="gallery-copy"><h2>' + _e(entry["name"]) + '</h2><p>' + _text(entry["description"]) + '</p><span class="gallery-slug">' + _e(theme["name"]) + '</span></div>' + swatch + '<span class="gallery-arrow" aria-hidden="true">↗</span></a></li>')
    content = '<main class="gallery-main"><div class="gallery-masthead"><span>HEIGE FEISHU WORD</span><span>' + f'{len(entries):02d}' + ' DOCUMENT SAMPLES</span></div><header class="gallery-intro"><h1>把重要的信息，写进一页好文档。</h1><p>六套白页样本，用清晰的层级、紧凑的图表和小面积主题色组织信息。选择沟通场景，查看完整的示范内容与数据口径。</p></header><ol class="gallery-list">' + "".join(parts) + '</ol><footer class="gallery-footer">本地样本按飞书白页的阅读结构设计。原生排版与可选 HTML 指标块的实际效果，需在目标客户端验证；示范数据均为合成内容。</footer></main>'
    return _document("HeiGe Feishu Word 文档模板集", get_theme("grid-bureau"), content, extra_css=_GALLERY_CSS)
