"""Offline HTML previews and optional, compact Feishu HTML overviews.

The preview is deliberately labelled: native Docx typography is controlled by
the Feishu client. User content only enters escaped text and attribute values.
No fonts, scripts, images, or stylesheets are fetched from the network.
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
_SERIF = '"Cormorant Garamond",Georgia,"Noto Serif SC","Songti SC","STSong",serif'
_MONO = '"IBM Plex Mono","SFMono-Regular",Menlo,"Noto Sans SC","PingFang SC",monospace'


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


def _text(value: Any) -> str:
    return _e(value).replace("\n", "<br>")


def _tokens(theme: dict) -> str:
    # Values come exclusively from the fixed theme registry, never user CSS.
    return ":root{" + ";".join(
        "--" + key + ":" + theme[key]
        for key in ("canvas", "surface", "ink", "muted", "hairline", "primary", "secondary")
    ) + ";--sans:" + _SANS + ";--serif:" + _SERIF + ";--mono:" + _MONO + ";}"


_CSS = r"""
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--canvas);color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.75;overflow-wrap:anywhere}button,a,summary{-webkit-tap-highlight-color:transparent}button{font:inherit}a{color:inherit;text-decoration-thickness:1px;text-underline-offset:4px}button,summary{cursor:pointer}button:focus-visible,a:focus-visible,summary:focus-visible,[tabindex]:focus-visible{outline:3px solid var(--primary);outline-offset:5px}p,h1,h2,h3,figure{margin:0}p+p{margin-top:1em}h1,h2,h3{text-wrap:balance;word-break:normal;overflow-wrap:anywhere}h1{font-size:clamp(38px,5.6vw,76px);line-height:1.16;letter-spacing:-.03em;font-weight:650;max-width:15em}h2{font-size:clamp(25px,3vw,36px);line-height:1.35;letter-spacing:-.015em}h3{font-size:21px;line-height:1.45}button{color:inherit}svg{display:block;max-width:100%;height:auto}main,.toolbar-inner{width:min(1120px,calc(100% - 96px));margin-inline:auto;min-width:0}.preview-notice{padding:12px 24px;background:var(--surface);border-bottom:1px solid var(--hairline);font-size:12px;color:var(--muted);text-align:center}.toolbar-inner{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:20px 0;font-size:12px;letter-spacing:.06em}.toolbar-label{font-weight:600}.quiet-button{border:1px solid var(--hairline);background:transparent;border-radius:2px;padding:7px 14px;font-size:13px;white-space:nowrap}.quiet-button:hover{background:var(--surface)}.hero{position:relative;padding:70px 0 64px;border-top:1px solid var(--hairline);isolation:isolate}.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:28px}.hero-title{position:relative}.hero-subtitle{max-width:42em;font-size:19px;line-height:1.8;margin-top:26px;color:var(--muted)}.meta{display:flex;flex-wrap:wrap;gap:12px 28px;margin-top:32px;font-size:13px;color:var(--muted)}.meta span{display:inline-flex;align-items:center;gap:8px}.meta .audience{flex-basis:100%}.signature{display:none}.toc{display:flex;flex-wrap:wrap;gap:14px 25px;padding:20px 0;border-top:1px solid var(--hairline);border-bottom:1px solid var(--hairline);font-size:12px}.toc a{text-decoration:none;display:inline-flex;gap:8px;align-items:baseline}.toc a:hover{text-decoration:underline}.toc .ordinal{color:var(--muted);font-family:var(--mono)}.doc-section{position:relative;margin-top:72px;min-width:0}.section-heading{display:flex;align-items:baseline;gap:18px;margin-bottom:26px}.section-no{font:12px/1.5 var(--mono);color:var(--muted);flex-shrink:0;letter-spacing:.06em}.section-content{min-width:0}.prose{max-width:48em}.prose p{white-space:normal}.callout{padding:28px 32px;border-left:3px solid var(--primary);background:var(--surface)}.callout-label{font-size:12px;letter-spacing:.1em;font-weight:650;margin-bottom:9px;color:var(--muted)}.callout p{font-size:20px;line-height:1.7}.callout[data-tone="risk"],.callout[data-tone="warning"]{border-left-style:double;border-left-width:5px}.metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));border-top:1px solid var(--hairline)}.metric{padding:28px 32px 28px 0;min-width:0;border-bottom:1px solid var(--hairline)}.metric:nth-child(even){padding-left:32px;border-left:1px solid var(--hairline)}.metric-label{font-size:14px;line-height:1.6;margin-bottom:14px}.metric-value{font-size:clamp(34px,5vw,64px);font-weight:550;line-height:1.1;letter-spacing:-.04em;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}.metric-note{margin-top:14px;font-size:13px;color:var(--muted)}.table-scroll{overflow-x:auto;width:100%;max-width:100%;border-top:1px solid var(--hairline);border-bottom:1px solid var(--hairline)}table{width:100%;border-collapse:collapse;text-align:left;font-size:14px;line-height:1.7}th,td{padding:15px 18px;border-bottom:1px solid var(--hairline);vertical-align:top;min-width:120px;overflow-wrap:anywhere}th{font-weight:650;background:var(--surface)}tr:last-child td{border-bottom:0}td:first-child{font-weight:550}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 40px}.grid-item{padding:24px 0;border-top:1px solid var(--hairline)}.grid-item p{font-size:16px;margin-top:12px}.grid-index{font:12px var(--mono);color:var(--muted);margin-bottom:13px}.actions{list-style:none;margin:0;padding:0}.action{display:grid;grid-template-columns:24px 1fr;gap:16px;padding:23px 0;border-top:1px solid var(--hairline)}.action-box{width:16px;height:16px;border:1px solid var(--muted);margin-top:7px}.action-task{font-size:18px}.action-meta{display:flex;gap:22px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-top:8px}.timeline{list-style:none;padding:0;margin:0}.milestone{display:grid;grid-template-columns:130px 25px minmax(0,1fr);gap:18px;position:relative;padding-bottom:34px}.milestone:last-child{padding-bottom:0}.milestone-date{font:13px/1.6 var(--mono);color:var(--muted);padding-top:4px}.milestone-marker{position:relative;display:flex;justify-content:center}.milestone-marker:after{content:"";position:absolute;top:18px;bottom:-35px;left:12px;width:1px;background:var(--hairline)}.milestone:last-child .milestone-marker:after{display:none}.milestone-dot{height:10px;width:10px;border:2px solid var(--muted);background:var(--canvas);border-radius:50%;margin-top:8px;position:relative;z-index:1}.milestone[data-status="done"] .milestone-dot,.milestone[data-status="active"] .milestone-dot{background:var(--primary);border-color:var(--primary)}.milestone[data-status="risk"] .milestone-dot{border-radius:0;transform:rotate(45deg)}.milestone-header{display:flex;align-items:baseline;justify-content:space-between;gap:18px}.milestone-status{font-size:12px;color:var(--muted);white-space:nowrap}.milestone p{margin-top:10px;font-size:15px}.recommendation{margin-top:22px;padding-left:18px;border-left:2px solid var(--primary);font-size:16px}.chart-insight{font-size:21px;line-height:1.65;margin-bottom:24px;max-width:45em}.diagram-scroll{max-width:100%;overflow-x:auto;background:var(--surface);border:1px solid var(--hairline)}.diagram-open{display:block;width:100%;min-width:660px;border:0;background:transparent;padding:0;text-align:left;color:inherit}.diagram-open svg{width:100%;max-width:none;height:auto}.figure-caption{display:flex;justify-content:space-between;gap:12px;margin-top:12px;font-size:12px;color:var(--muted)}.figure-caption span{min-width:0}.figure-caption .figure-hint{flex-shrink:0}details{margin-top:20px}summary{font-size:13px;color:var(--muted);padding:8px 0}details[open] summary{margin-bottom:8px}.workflow-list{padding-left:1.5em;font-size:15px}.workflow-list li{padding:8px 0}.workflow-list strong{display:block}.document-footer{margin-top:88px;padding:28px 0 40px;border-top:1px solid var(--hairline);font-size:12px;color:var(--muted)}.footer-mark{margin-top:20px;font:11px var(--mono);letter-spacing:.13em}.figure-dialog{width:min(1400px,94vw);max-width:94vw;max-height:92vh;border:1px solid var(--hairline);background:var(--canvas);color:var(--ink);padding:0}.figure-dialog::backdrop{background:rgba(0,0,0,.72)}.dialog-controls{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 24px;border-bottom:1px solid var(--hairline)}.dialog-controls strong{font-size:15px}.dialog-buttons{display:flex;gap:8px;flex-shrink:0}.dialog-scroll{overflow:auto;max-height:75vh;padding:20px}.dialog-art{width:100%;min-width:0;transform-origin:top left}.dialog-art svg{width:100%;max-width:none}.overview main{width:100%;padding:32px;max-width:1120px}.overview .hero{padding-top:36px}.overview .doc-section{margin-top:32px}.overview .document-footer{margin-top:30px;padding-bottom:0}
/* Atelier: a single drawn gold rule and generous typographic air. */
body[data-layout="editorial"] h1,body[data-layout="editorial"] h2,body[data-layout="editorial"] .metric-value{font-family:var(--serif);font-weight:400}body[data-layout="editorial"] .hero{padding-top:94px;padding-bottom:84px}body[data-layout="editorial"] .signature{display:block;width:48px;height:1px;background:var(--primary);margin:0 0 32px;transform-origin:left;animation:rule-draw .28s ease-out both}body[data-layout="editorial"] .doc-section{margin-top:88px}body[data-layout="editorial"] .metric-value{font-size:clamp(42px,5.8vw,76px)}body[data-layout="editorial"] .callout{border-left:1px solid var(--hairline);padding:28px 36px;background:transparent}body[data-layout="editorial"] .callout p{font-family:var(--serif);font-size:25px}
/* Grid Bureau: numbered reference rail, exposed baseline, filing stamp. */
body[data-layout="ledger"] main{padding-left:96px;background-image:repeating-linear-gradient(to bottom,transparent 0,transparent 7px,rgba(91,98,112,.035) 7px,rgba(91,98,112,.035) 8px)}body[data-layout="ledger"] .hero{border-top:4px solid var(--ink);padding:48px 0}body[data-layout="ledger"] h1{font-weight:800;letter-spacing:-.04em}body[data-layout="ledger"] .hero .eyebrow{display:inline-block;background:var(--secondary);color:#fff;padding:10px 16px}body[data-layout="ledger"] .section-no{position:absolute;left:-96px;top:6px;width:70px;border-top:1px solid var(--hairline);padding-top:8px}body[data-layout="ledger"] .section-no:before{content:"§ "}body[data-layout="ledger"] .metric-value{font-family:var(--mono);font-weight:700}body[data-layout="ledger"] .section-heading{border-top:1px solid var(--ink);padding-top:20px}body[data-layout="ledger"] .grid{gap:0 24px}body[data-layout="ledger"] .callout{background:var(--surface);border:1px solid var(--hairline);border-left:4px solid var(--primary)}
/* Nocturne: one static light shaft, one status signal, quiet dark field. */
body[data-layout="nocturne"] .hero{padding:80px 0;overflow:hidden;background-image:linear-gradient(rgba(32,38,47,.3) 1px,transparent 1px),linear-gradient(90deg,rgba(32,38,47,.3) 1px,transparent 1px);background-size:48px 48px}body[data-layout="nocturne"] .hero:before{content:"";position:absolute;z-index:-1;inset:-30% -10% 5% 30%;background:radial-gradient(ellipse at 85% 25%,rgba(45,212,191,.20),transparent 64%);transform:rotate(-18deg)}body[data-layout="nocturne"] h1{font-family:"Geist",var(--sans);font-weight:600;max-width:13em}body[data-layout="nocturne"] .eyebrow:before{content:"";display:inline-block;width:7px;height:7px;background:#5ff0dc;border-radius:50%;margin-right:12px;box-shadow:0 0 13px rgba(45,212,191,.4);animation:signal-arrive 1.2s ease-out both}body[data-layout="nocturne"] .metric-value{font-family:"JetBrains Mono",var(--mono);font-weight:500}body[data-layout="nocturne"] .metric:first-child .metric-value{color:var(--secondary)}body[data-layout="nocturne"] .metrics{border:0;gap:16px}body[data-layout="nocturne"] .metric{background:var(--surface);padding:28px;border:1px solid var(--hairline);border-radius:10px}body[data-layout="nocturne"] .callout{border-radius:0 10px 10px 0}body[data-layout="nocturne"] .diagram-scroll{border-radius:10px}
/* Broadsheet: masthead rules, editorial columns and a genuine drop cap. */
body[data-layout="press"]{font-family:"Newsreader",var(--serif)}body[data-layout="press"] .hero{border-top:5px double var(--ink);border-bottom:1px solid var(--ink);padding:36px 0 40px}body[data-layout="press"] .hero .eyebrow{font-family:"Archivo",var(--sans);font-weight:650;background:var(--primary);color:#faf8f3;width:fit-content;padding:5px 11px;margin-top:-50px;margin-bottom:33px}body[data-layout="press"] h1{font-family:"Playfair Display",var(--serif);font-weight:900;letter-spacing:-.025em;font-size:clamp(42px,6vw,80px)}body[data-layout="press"] h2{font-weight:800}body[data-layout="press"] .hero-subtitle{font-size:21px;color:var(--ink)}body[data-layout="press"] .toc{border-top:0;border-bottom:3px double var(--ink);font-family:var(--sans)}body[data-layout="press"] .section-heading{border-top:3px double var(--ink);padding-top:20px}body[data-layout="press"] .prose{column-count:2;column-gap:36px;column-rule:1px solid var(--hairline);max-width:none}body[data-layout="press"] .prose p:first-child:first-letter{float:left;font-size:4.2em;line-height:.88;padding:8px 10px 0 0;font-weight:900;color:var(--primary)}body[data-layout="press"] .grid{column-gap:0}body[data-layout="press"] .grid-item{padding:22px 28px 22px 0}body[data-layout="press"] .grid-item:nth-child(even){border-left:1px solid var(--hairline);padding-left:28px}body[data-layout="press"] .metric-value{font-family:var(--mono)}body[data-layout="press"] .callout{background:transparent;border-left:0;border-top:1px solid var(--hairline);border-bottom:1px solid var(--hairline);padding:24px 0}body[data-layout="press"] .callout p{font-size:25px}.meta,.toolbar-inner,.preview-notice{font-family:var(--sans)}
/* Moxi: the headline sits in the ink; the only red is its small seal. */
body[data-layout="ink"]{line-height:1.9}body[data-layout="ink"] .hero{padding:58px 0 80px;border:0}body[data-layout="ink"] .eyebrow{font-family:"LXGW WenKai","Kaiti SC","Noto Serif SC","Songti SC",serif;font-size:14px;letter-spacing:.3em}body[data-layout="ink"] .hero-title{max-width:850px;padding:48px 68px 54px 38px;isolation:isolate}body[data-layout="ink"] .hero-title:before{content:"";position:absolute;inset:-8px -5px -10px -24px;z-index:-1;background:radial-gradient(ellipse at 32% 55%,#1c1a17 0 63%,rgba(28,26,23,.94) 70%,rgba(28,26,23,.6) 77%,transparent 88%);border-radius:43% 34% 39% 22% / 24% 45% 28% 38%;transform:rotate(-1deg)}body[data-layout="ink"] h1{font-family:"Noto Serif SC","Songti SC","STSong",serif;font-size:clamp(38px,5vw,66px);font-weight:900;color:#f6f1e4;line-height:1.35;letter-spacing:.02em;max-width:13em}body[data-layout="ink"] .signature{display:flex;position:absolute;right:2px;bottom:0;width:56px;height:56px;align-items:center;justify-content:center;background:#c8483a;color:#f6f1e4;font:24px/1.1 "Noto Serif SC","Songti SC",serif;transform:rotate(-3deg);z-index:1}body[data-layout="ink"] .hero-subtitle{margin-top:44px;max-width:34em}body[data-layout="ink"] h2,body[data-layout="ink"] h3,body[data-layout="ink"] .metric-value{font-family:"Noto Serif SC","Songti SC","STSong",serif}body[data-layout="ink"] .prose{max-width:36em}body[data-layout="ink"] .doc-section{margin-top:96px}body[data-layout="ink"] .section-heading{gap:26px}body[data-layout="ink"] .section-no{font-family:var(--serif);font-size:32px;color:var(--muted);font-weight:400}body[data-layout="ink"] .callout{background:var(--ink);color:var(--canvas);border:0;padding:40px;border-radius:4px}body[data-layout="ink"] .callout-label{color:var(--hairline)}body[data-layout="ink"] .callout p{font-family:"LXGW WenKai","Kaiti SC","Noto Serif SC","Songti SC",serif;font-size:25px}body[data-layout="ink"] .metric{padding-block:36px}body[data-layout="ink"] .metric-value{font-weight:800}
/* Soundwave: flat pink, a yellow lead number and 24 frozen waveform bars. */
body[data-layout="festival"] h1{font-family:"Anton","Archivo Black",Impact,"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;font-weight:900;letter-spacing:-.04em;line-height:1.12;font-size:clamp(42px,6.5vw,86px)}body[data-layout="festival"] .hero{padding:46px 40px 0;background:#ff2d95;color:#140f14;border:0}body[data-layout="festival"] .hero .eyebrow,body[data-layout="festival"] .hero-subtitle,body[data-layout="festival"] .hero .meta{color:#140f14}body[data-layout="festival"] .hero .eyebrow{background:#ffe500;display:inline-block;padding:7px 14px;font-weight:700;transform:rotate(-2deg)}body[data-layout="festival"] .hero-subtitle{max-width:38em;font-weight:500}body[data-layout="festival"] .signature{display:flex;height:110px;gap:6px;align-items:flex-end;margin-top:36px;overflow:hidden}body[data-layout="festival"] .wavebar{display:block;flex:1;min-width:0;background:#140f14;height:var(--h);transform-origin:bottom;animation:wave-arrive .6s ease-out both;animation-delay:var(--delay)}body[data-layout="festival"] .wavebar:nth-child(3n){background:#ffe500}body[data-layout="festival"] .wavebar:nth-child(3n + 2){background:#1e4dff}body[data-layout="festival"] .metrics{gap:16px;border:0;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr)}body[data-layout="festival"] .metric{padding:30px;background:var(--surface);border:0}body[data-layout="festival"] .metric:first-child{background:#ffe500;color:#140f14;grid-row:span 2;display:flex;flex-direction:column;justify-content:center;min-height:260px}body[data-layout="festival"] .metric:first-child .metric-note{color:#140f14}body[data-layout="festival"] .metric-value{font-family:"Anton","Archivo Black",Impact,"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;font-weight:900;letter-spacing:-.03em}body[data-layout="festival"] .metric:first-child .metric-value{font-size:clamp(48px,7vw,94px)}body[data-layout="festival"] .section-no{color:#ffe500;font-size:21px;font-weight:700}body[data-layout="festival"] .doc-section{margin-top:64px}body[data-layout="festival"] .grid-item{padding:28px;background:var(--surface);border:0}body[data-layout="festival"] .grid{gap:16px}body[data-layout="festival"] .callout{border-left-color:#ffe500}
@keyframes rule-draw{from{transform:scaleX(0);opacity:0}to{transform:scaleX(1);opacity:1}}@keyframes signal-arrive{from{transform:scale(.65);opacity:.3}to{transform:scale(1);opacity:1}}@keyframes wave-arrive{from{transform:scaleY(.12);opacity:.6}to{transform:scaleY(1);opacity:1}}
@media(max-width:767px){body{font-size:16px}main,.toolbar-inner{width:calc(100% - 40px)}.preview-notice{font-size:11px;padding:10px 20px;text-align:left}.toolbar-inner{padding-block:15px;gap:16px}.hero{padding:40px 0}h1{font-size:clamp(34px,8vw,54px);line-height:1.24}.hero-subtitle{font-size:17px;margin-top:24px}.eyebrow{margin-bottom:22px}.meta{font-size:12px;margin-top:26px;gap:10px 18px}.toc{gap:10px 17px;font-size:11px}.doc-section{margin-top:48px}.section-heading{gap:12px;margin-bottom:22px}h2{font-size:26px}.metrics{grid-template-columns:1fr}.metric,.metric:nth-child(even){padding:23px 0;border-left:0}.metric-value{font-size:48px}.metric-label{margin-bottom:9px}.metric-note{margin-top:10px}.grid{grid-template-columns:1fr;gap:0}.callout{padding:24px}.callout p{font-size:18px}.milestone{grid-template-columns:18px minmax(0,1fr);gap:12px;padding-bottom:30px}.milestone-date{grid-column:2;grid-row:auto;margin-bottom:-5px}.milestone-marker{grid-column:1;grid-row:span 2}.milestone-marker:after{left:8px;bottom:-32px}.milestone-content{grid-column:2}.milestone-header{display:block}.milestone-status{display:block;margin-top:5px}.milestone h3{font-size:20px}.diagram-open{min-width:640px}.figure-caption{display:block}.figure-caption .figure-hint{display:block;margin-top:5px}.dialog-controls{padding:12px;align-items:flex-start;gap:12px}.dialog-buttons{gap:5px}.dialog-buttons .quiet-button{font-size:12px;padding:6px 9px}.dialog-scroll{padding:8px}.document-footer{margin-top:56px}.overview main{padding:20px}.overview .hero{padding-top:24px}body[data-layout="editorial"] .hero{padding:52px 0}body[data-layout="editorial"] .doc-section{margin-top:56px}body[data-layout="ledger"] main{padding-left:0}body[data-layout="ledger"] .section-no{position:static;width:auto;padding:0;border:0}body[data-layout="ledger"] .section-heading{display:block;padding-top:16px}body[data-layout="ledger"] .section-heading h2{margin-top:10px}body[data-layout="ledger"] .hero{padding:32px 0}body[data-layout="nocturne"] .hero{padding:44px 0;background-size:64px 64px}body[data-layout="nocturne"] .hero:before{inset:-10% -20% 10% -20%;transform:none;background:radial-gradient(ellipse at 50% 0%,rgba(45,212,191,.18),transparent 68%)}body[data-layout="nocturne"] .metric{padding:25px}body[data-layout="press"] .hero{padding-top:29px}body[data-layout="press"] .hero .eyebrow{margin-top:-43px}body[data-layout="press"] h1{font-size:42px;text-align:left}body[data-layout="press"] .prose{column-count:1}body[data-layout="press"] .grid-item,body[data-layout="press"] .grid-item:nth-child(even){border-left:0;padding:22px 0}body[data-layout="press"] .prose p:first-child:first-letter{font-size:3.5em}body[data-layout="ink"] .hero{padding:28px 0 44px}body[data-layout="ink"] .hero-title{padding:35px 26px 38px 17px}body[data-layout="ink"] h1{font-size:clamp(30px,7.5vw,44px)}body[data-layout="ink"] .hero-title:before{inset:-5px -4px -8px -9px}body[data-layout="ink"] .signature{width:42px;height:42px;font-size:20px;right:2px;bottom:-17px}body[data-layout="ink"] .hero-subtitle{margin-top:35px}body[data-layout="ink"] .doc-section{margin-top:60px}body[data-layout="ink"] .callout{padding:27px}body[data-layout="ink"] .callout p{font-size:22px}body[data-layout="festival"] .hero{padding:30px 22px 0}body[data-layout="festival"] h1{font-size:clamp(38px,9vw,60px)}body[data-layout="festival"] .signature{height:72px;gap:3px;margin-top:28px}body[data-layout="festival"] .metrics{grid-template-columns:1fr}body[data-layout="festival"] .metric:first-child{min-height:225px;grid-row:auto}body[data-layout="festival"] .metric,body[data-layout="festival"] .metric:nth-child(even){padding:27px}body[data-layout="festival"] .metric:first-child .metric-value{font-size:64px}}
@media(max-width:600px){.dialog-controls{flex-direction:column;align-items:stretch;gap:10px;padding:16px}.dialog-buttons{justify-content:flex-end}.dialog-controls strong{overflow-wrap:anywhere}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{animation:none!important;transition:none!important}}
@media print{.preview-notice,.toolbar,.toc,.figure-hint,.figure-dialog{display:none!important}body{background:#fff;color:#111;font-size:11pt}main{width:100%;padding:0!important}.hero{padding-block:24px!important}.doc-section{margin-top:32px!important;break-inside:avoid-page}.diagram-open{min-width:0}.diagram-scroll,.table-scroll{overflow:visible}.figure-caption{font-size:9pt}h1{font-size:30pt!important}h2{font-size:20pt!important}details:not([open])>*:not(summary){display:revert}summary{display:none}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


_JS = r"""
(()=>{'use strict';
const printButton=document.querySelector('[data-print]');
if(printButton)printButton.addEventListener('click',()=>window.print());
const dialog=document.getElementById('figure-dialog');
if(!dialog)return;
const art=dialog.querySelector('.dialog-art');
const label=dialog.querySelector('#figure-dialog-title');
let factor=1;
const resize=()=>{art.style.width=(factor*100)+'%';};
document.querySelectorAll('.diagram-open').forEach(button=>{
button.addEventListener('click',()=>{
const original=button.querySelector('svg');if(!original)return;
const copy=original.cloneNode(true);
// Avoid collisions with the original SVG's fragment identifiers.
const remap=new Map();copy.querySelectorAll('[id]').forEach(node=>{const old=node.id;const next='zoom-'+old;remap.set(old,next);node.id=next;});
copy.querySelectorAll('*').forEach(node=>Array.from(node.attributes).forEach(attr=>{
let value=attr.value;remap.forEach((next,old)=>{value=value.split('url(#'+old+')').join('url(#'+next+')');if(value==='#'+old)value='#'+next;});
if(value!==attr.value)node.setAttribute(attr.name,value);
}));
art.replaceChildren(copy);label.textContent=button.dataset.title;factor=1;resize();
if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','');
dialog.querySelector('.dialog-scroll').scrollTo(0,0);
});});
dialog.querySelector('[data-close]').addEventListener('click',()=>{if(typeof dialog.close==='function')dialog.close();else dialog.removeAttribute('open');});
dialog.querySelector('[data-enlarge]').addEventListener('click',()=>{factor=Math.min(3,factor+.25);resize();});
dialog.querySelector('[data-fit]').addEventListener('click',()=>{factor=1;resize();});
dialog.addEventListener('click',event=>{if(event.target===dialog){const box=dialog.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)dialog.close();}});
})();
"""


def _signature(theme: dict) -> str:
    if theme["layout"] == "festival":
        heights = [24, 43, 68, 39, 82, 100, 71, 48, 86, 61, 37, 77,
                   100, 55, 31, 65, 89, 73, 44, 97, 60, 83, 46, 25]
        return '<div class="signature" aria-hidden="true">' + "".join(
            f'<i class="wavebar" style="--h:{height}%;--delay:{i * 12}ms"></i>'
            for i, height in enumerate(heights)
        ) + "</div>"
    if theme["layout"] == "ink":
        return '<span class="signature" aria-hidden="true">鉴</span>'
    return '<div class="signature" aria-hidden="true"></div>'


def _hero(meta: dict, theme: dict) -> str:
    eyebrow = '<p class="eyebrow">' + _text(meta.get("eyebrow", theme["name"])) + "</p>"
    title = '<div class="hero-title"><h1>' + _text(meta["title"]) + "</h1>"
    if theme["layout"] == "ink":
        title += _signature(theme)
    title += "</div>"
    subtitle = '<p class="hero-subtitle">' + _text(meta["subtitle"]) + "</p>" if meta.get("subtitle") else ""
    metadata = []
    for key in ("status", "reading_time"):
        if meta.get(key):
            metadata.append("<span>" + _text(meta[key]) + "</span>")
    if meta.get("audience"):
        metadata.append('<span class="audience">适用读者：' + _text("、".join(meta["audience"])) + "</span>")
    before = _signature(theme) if theme["layout"] == "editorial" else ""
    after = _signature(theme) if theme["layout"] == "festival" else ""
    return '<header class="hero">' + eyebrow + before + title + subtitle + '<div class="meta">' + "".join(metadata) + "</div>" + after + "</header>"


def _table(columns: list, rows: list, label: str) -> str:
    head = "".join('<th scope="col">' + _text(value) + "</th>" for value in columns)
    body = "".join("<tr>" + "".join("<td>" + _text(value) + "</td>" for value in row) + "</tr>" for row in rows)
    return '<div class="table-scroll" tabindex="0" role="region" aria-label="' + _e(label) + '"><table><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table></div>"


def _metrics(section: dict) -> str:
    return '<div class="metrics">' + "".join(
        '<article class="metric"><p class="metric-label">' + _text(item["label"]) +
        '</p><p class="metric-value">' + _text(item["value"]) +
        '</p><p class="metric-note">' + _text(item["note"]) + "</p></article>"
        for item in section["items"]
    ) + "</div>"


def _figure(svg: str, title: str, caption: str = "") -> str:
    return '<figure><div class="diagram-scroll"><button class="diagram-open" type="button" data-title="' + _e(title) + '" aria-label="' + _e("查看大图：" + title) + '">' + svg + '</button></div><figcaption class="figure-caption"><span>' + _text(caption) + '</span><span class="figure-hint">点击查看大图，窄屏可横向滑动</span></figcaption></figure>'


def _section_content(section: dict, theme: dict) -> str:
    kind = section["type"]
    if kind == "prose":
        return '<div class="prose">' + "".join("<p>" + _text(p) + "</p>" for p in section["paragraphs"]) + "</div>"
    if kind == "callout":
        tone = section.get("tone", "info")
        return '<aside class="callout" data-tone="' + _e(tone) + '"><div class="callout-label">' + _TONE[tone] + "</div><p>" + _text(section["body"]) + "</p></aside>"
    if kind == "metrics":
        return _metrics(section)
    if kind == "table":
        return _table(section["columns"], section["rows"], section["title"])
    if kind == "grid":
        return '<div class="grid">' + "".join('<article class="grid-item"><div class="grid-index">' + f'{i + 1:02d}' + "</div><h3>" + _text(item["title"]) + "</h3><p>" + _text(item["body"]) + "</p></article>" for i, item in enumerate(section["items"])) + "</div>"
    if kind == "actions":
        return '<ol class="actions">' + "".join('<li class="action"><span class="action-box" aria-hidden="true"></span><div><p class="action-task">' + _text(item["action"]) + '</p><p class="action-meta"><span>负责人：' + _text(item["owner"]) + "</span><span>截止：" + _text(item["due"]) + "</span></p></div></li>" for item in section["items"]) + "</ol>"
    if kind == "timeline":
        return '<ol class="timeline">' + "".join('<li class="milestone" data-status="' + _e(item["status"]) + '"><time class="milestone-date">' + _text(item["date"]) + '</time><div class="milestone-marker" aria-hidden="true"><span class="milestone-dot"></span></div><div class="milestone-content"><div class="milestone-header"><h3>' + _text(item["title"]) + '</h3><span class="milestone-status">' + _STATUS[item["status"]] + "</span></div><p>" + _text(item["body"]) + "</p></div></li>" for item in section["items"]) + "</ol>"
    if kind == "comparison":
        return _table(["评估维度"] + section["options"], [[row["label"]] + row["values"] for row in section["criteria"]], section["title"]) + '<p class="recommendation"><strong>建议：</strong>' + _text(section["recommendation"]) + "</p>"
    if kind == "whiteboard_workflow":
        from .svg_renderer import render_workflow_svg
        svg = render_workflow_svg(section, theme)
        steps = "".join("<li><strong>" + _text(step["title"]) + "</strong>" + _text(step["description"]) + "</li>" for step in section["steps"])
        return _figure(svg, section["title"]) + '<details><summary>查看流程文字</summary><ol class="workflow-list">' + steps + "</ol></details>"
    if kind == "chart":
        from .charts import chart_table, render_chart_svg
        columns, rows = chart_table(section)
        caption = "数据来源：" + section["source"] + "。图表为本次输入的静态快照。"
        if section.get("unit"):
            caption = "单位：" + section["unit"] + "。" + caption
        return '<p class="chart-insight">' + _text(section["insight"]) + "</p>" + _figure(render_chart_svg(section, theme), section["title"], caption) + '<details><summary>查看完整数据表</summary>' + _table(columns, rows, section["title"] + "数据表") + "</details>"
    raise ValueError("unsupported preview section type: " + kind)


def _section(section: dict, theme: dict, index: int) -> str:
    return '<section class="doc-section" id="section-' + _e(section["id"]) + '" data-section-type="' + _e(section["type"]) + '"><div class="section-heading"><span class="section-no">' + f'{index:02d}' + "</span><h2>" + _text(section["title"]) + '</h2></div><div class="section-content">' + _section_content(section, theme) + "</div></section>"


def _footer(meta: dict, credit: bool = True) -> str:
    disclaimer = "<p>" + _text(meta["disclaimer"]) + "</p>" if meta.get("disclaimer") else ""
    mark = '<p class="footer-mark">HEIGE FEISHU WORD</p>' if credit else ""
    return '<footer class="document-footer">' + disclaimer + mark + "</footer>" if disclaimer or mark else ""


def _document(title: str, theme: dict, content: str, overview: bool = False, extra_css: str = "", script: str = "") -> str:
    metas = '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
    if overview:
        metas += '<meta name="use-iframe" content="true"><meta name="html-box-height-mode" content="auto"><meta name="description" content="' + _e(title + "的核心结论与指标概览") + '">'
    return '<!doctype html><html lang="zh-CN"><head>' + metas + "<title>" + _e(title) + "</title><style>" + _tokens(theme) + _CSS + extra_css + '</style></head><body data-theme="' + theme["slug"] + '" data-layout="' + theme["layout"] + '"' + (' class="overview"' if overview else "") + ">" + content + ("<script>" + script + "</script>" if script else "") + "</body></html>\n"


def render_preview_html(body: Dict[str, Any]) -> str:
    """Render every validated section as an offline, responsive design preview."""
    validate_body(body)
    theme = get_theme(body.get("theme"))
    meta = body["meta"]
    notice = '<div class="preview-notice">本地设计预览，飞书原生正文以客户端渲染为准</div>'
    toolbar = '<div class="toolbar"><div class="toolbar-inner"><span class="toolbar-label">' + _e(theme["name"]) + '</span><button class="quiet-button" type="button" data-print>打印预览</button></div></div>'
    toc = '<nav class="toc" aria-label="文档目录">' + "".join('<a href="#section-' + _e(section["id"]) + '"><span class="ordinal">' + f'{i + 1:02d}' + "</span><span>" + _text(section["title"]) + "</span></a>" for i, section in enumerate(body["sections"])) + "</nav>"
    content = notice + toolbar + "<main>" + _hero(meta, theme) + toc + "".join(_section(section, theme, i + 1) for i, section in enumerate(body["sections"])) + _footer(meta) + "</main>"
    content += '<dialog class="figure-dialog" id="figure-dialog" aria-labelledby="figure-dialog-title"><div class="dialog-controls"><strong id="figure-dialog-title">图表大图</strong><div class="dialog-buttons"><button type="button" class="quiet-button" data-enlarge aria-label="放大图表">放大</button><button type="button" class="quiet-button" data-fit>适应宽度</button><button type="button" class="quiet-button" data-close autofocus>关闭</button></div></div><div class="dialog-scroll" tabindex="0" role="region" aria-label="图表大图，可滚动查看"><div class="dialog-art"></div></div></dialog>'
    return _document(meta["title"], theme, content, script=_JS)


def render_overview_html(body: Dict[str, Any]) -> str:
    """Render hero, all metadata and the first KPI section for html5-block.

    This intentionally has no local navigation, controls or external resources.
    Its visual rendering in a Feishu tenant still needs a cloud acceptance test.
    """
    validate_body(body)
    theme = get_theme(body.get("theme"))
    content = "<main>" + _hero(body["meta"], theme)
    for index, section in enumerate(body["sections"], 1):
        if section["type"] == "metrics":
            content += _section(section, theme, index)
            break
    content += _footer(body["meta"], credit=False) + "</main>"
    result = _document(body["meta"]["title"], theme, content, overview=True)
    if len(result.encode("utf-8")) > 500_000:
        raise ValueError("HTML overview exceeds the 500 KB Feishu content limit")
    return result


_GALLERY_CSS = r"""
.gallery-main{padding-top:40px}.gallery-masthead{display:flex;align-items:center;justify-content:space-between;gap:24px;font:12px var(--mono);letter-spacing:.13em;border-bottom:1px solid var(--hairline);padding-bottom:20px}.gallery-intro{padding:82px 0 60px;max-width:830px}.gallery-intro h1{font-family:var(--serif);font-weight:400;font-size:clamp(44px,6.5vw,84px);max-width:12em}.gallery-intro p{max-width:37em;margin-top:26px;color:var(--muted)}.gallery-rule{height:1px;width:48px;background:var(--primary);margin-bottom:30px;transform-origin:left;animation:rule-draw .28s ease-out both}.gallery-list{list-style:none;padding:0;margin:0}.gallery-entry{display:grid;grid-template-columns:60px minmax(0,1fr) minmax(200px,.8fr) 46px;gap:24px;align-items:center;border-top:1px solid var(--hairline);padding:34px 0;text-decoration:none}.gallery-entry:hover .gallery-arrow{transform:translateX(5px)}.gallery-entry:hover h2{text-decoration:underline;text-underline-offset:6px;text-decoration-thickness:1px}.gallery-number{font:13px var(--mono);color:var(--muted);align-self:start;padding-top:8px}.gallery-copy h2{font-family:var(--serif);font-weight:500;font-size:30px}.gallery-copy p{font-size:14px;line-height:1.75;color:var(--muted);margin-top:12px;max-width:30em}.gallery-slug{display:block;font:10px var(--mono);letter-spacing:.07em;color:var(--muted);margin-top:18px}.gallery-arrow{font-size:25px;transition:transform .18s ease-out}.gallery-swatch{height:150px;position:relative;overflow:hidden;background:var(--swatch-canvas);border:1px solid var(--swatch-hairline);padding:24px;color:var(--swatch-ink);display:flex;flex-direction:column;justify-content:space-between}.swatch-line{width:36px;height:2px;background:var(--swatch-primary)}.swatch-title{font-family:var(--serif);font-size:28px;font-weight:600;line-height:1.2}.swatch-bars{display:flex;gap:7px;height:19px;align-items:end}.swatch-bars i{height:100%;width:25%;background:var(--swatch-primary)}.swatch-bars i:nth-child(2){height:70%;background:var(--swatch-ink)}.swatch-bars i:nth-child(3){height:40%;background:var(--swatch-hairline)}.gallery-swatch[data-preview-layout="ledger"]{padding-left:40px;background-image:repeating-linear-gradient(to bottom,transparent 0,transparent 7px,rgba(91,98,112,.08) 7px,rgba(91,98,112,.08) 8px)}.gallery-swatch[data-preview-layout="ledger"]:before{content:"§";position:absolute;left:14px;top:20px;font:14px var(--mono)}.gallery-swatch[data-preview-layout="ledger"] .swatch-title{font-family:var(--sans);font-weight:800}.gallery-swatch[data-preview-layout="nocturne"]{background-image:radial-gradient(ellipse at top right,rgba(45,212,191,.20),transparent 70%)}.gallery-swatch[data-preview-layout="nocturne"] .swatch-title{font-family:var(--mono);font-weight:500}.gallery-swatch[data-preview-layout="nocturne"] .swatch-line{width:6px;height:6px;border-radius:50%}.gallery-swatch[data-preview-layout="press"]{border-top:5px double var(--swatch-ink)}.gallery-swatch[data-preview-layout="press"] .swatch-line{width:100%;background:var(--swatch-ink);height:1px}.gallery-swatch[data-preview-layout="ink"] .swatch-title{background:var(--swatch-ink);color:var(--swatch-canvas);padding:5px 12px;width:fit-content}.gallery-swatch[data-preview-layout="ink"] .swatch-line{position:absolute;right:18px;bottom:19px;width:16px;height:16px;background:#c8483a}.gallery-swatch[data-preview-layout="festival"]{background:#ff2d95;color:#140f14;border:0}.gallery-swatch[data-preview-layout="festival"] .swatch-title{font-family:var(--sans);font-weight:900}.gallery-swatch[data-preview-layout="festival"] .swatch-line{background:#ffe500;height:8px;width:46px}.gallery-swatch[data-preview-layout="festival"] .swatch-bars i:first-child{background:#ffe500}.gallery-swatch[data-preview-layout="festival"] .swatch-bars i:nth-child(2){background:#1e4dff}.gallery-swatch[data-preview-layout="festival"] .swatch-bars i:nth-child(3){background:#140f14}.gallery-footer{padding:30px 0 50px;border-top:1px solid var(--hairline);font-size:12px;color:var(--muted)}
@media(max-width:767px){.gallery-main{padding-top:24px}.gallery-masthead{font-size:10px;gap:16px}.gallery-intro{padding:48px 0 38px}.gallery-intro h1{font-size:clamp(34px,9vw,46px)}.gallery-entry{grid-template-columns:30px minmax(0,1fr) 24px;gap:14px;padding:26px 0}.gallery-copy h2{font-size:28px}.gallery-swatch{grid-column:2;grid-row:2;height:122px;margin-top:4px}.gallery-arrow{grid-column:3;grid-row:1}.gallery-number{grid-row:1}.gallery-copy p{font-size:13px}.gallery-slug{font-size:10px}.gallery-swatch .swatch-title{font-size:25px}}
"""


def render_gallery_html(entries: Iterable[Dict[str, Any]]) -> str:
    """Render an editorial collection linking to each slug/preview.html."""
    entries = list(entries)
    parts = []
    for index, entry in enumerate(entries, 1):
        slug = str(entry["slug"])
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", slug):
            raise ValueError("gallery slug must be a safe local directory name")
        supplied_theme = entry.get("theme", slug)
        # Even a theme dictionary must resolve through the trusted registry.
        theme = get_theme(supplied_theme.get("slug") if isinstance(supplied_theme, dict) else supplied_theme)
        colors = ";".join("--swatch-" + key + ":" + theme[key] for key in ("canvas", "ink", "primary", "hairline"))
        swatch = '<div class="gallery-swatch" aria-hidden="true" data-preview-layout="' + theme["layout"] + '" style="' + colors + '"><span class="swatch-line"></span><span class="swatch-title">' + _e(theme["name"]) + '</span><span class="swatch-bars"><i></i><i></i><i></i></span></div>'
        parts.append('<li><a class="gallery-entry" href="' + _e(slug) + '/preview.html"><span class="gallery-number">' + f'{index:02d}' + '</span><div class="gallery-copy"><h2>' + _e(entry["name"]) + '</h2><p>' + _text(entry["description"]) + '</p><span class="gallery-slug">' + _e(theme["slug"]) + '</span></div>' + swatch + '<span class="gallery-arrow" aria-hidden="true">↗</span></a></li>')
    content = '<main class="gallery-main"><div class="gallery-masthead"><span>HEIGE FEISHU WORD</span><span>' + f'{len(entries):02d}' + ' VISUAL EDITIONS</span></div><header class="gallery-intro"><div class="gallery-rule" aria-hidden="true"></div><h1>让重要的信息，<br>拥有自己的样子。</h1><p>从管理简报到项目战报，选择适合这次沟通的视觉语言。打开完整样本，查看内容结构、图表与阅读节奏。</p></header><ol class="gallery-list">' + "".join(parts) + '</ol><footer class="gallery-footer">离线设计样本。飞书原生正文以客户端渲染为准；HTML 增强块需在目标租户验证。</footer></main>'
    return _document("HeiGe Feishu Word 视觉模板集", get_theme("atelier-bone"), content, extra_css=_GALLERY_CSS)
