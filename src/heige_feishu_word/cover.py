"""Six deterministic opening boards, not the separate Feishu cover resource."""
from html import escape
from .model import BodyValidationError


def _wrap(text, width):
    lines, line, size = [], '', 0
    for c in text:
        weight = 1 if ord(c) > 255 else 0.6
        if size + weight > width or c == '\n':
            lines.append(line)
            line, size = '', 0
        if c != '\n':
            line += c
            size += weight
    if line:
        lines.append(line)
    # Avoid a single CJK character or punctuation stranded on the final line.
    if len(lines)>1 and len(lines[-1])<=2:
        tail=lines[-2]+lines[-1]
        measure=lambda s:sum(1 if ord(c)>255 else .6 for c in s)
        breaks=[i+1 for i,c in enumerate(tail) if c in '，；。' and 4<=measure(tail[:i+1])<=width and 4<=measure(tail[i+1:])<=width]
        if breaks:
            split=min(breaks,key=lambda i:abs(measure(tail[:i])-measure(tail[i:])))
            lines[-2:]=[tail[:split],tail[split:]]
        else:
            while len(lines[-1])<4 and len(lines[-2])>1 and ord(lines[-2][-1])>255:
                lines[-1]=lines[-2][-1]+lines[-1]
                lines[-2]=lines[-2][:-1]
    return lines


def _text(text, x, y, size, color, width, max_lines, weight=400):
    lines = _wrap(str(text), width)
    if len(lines) > max_lines:
        raise BodyValidationError('opening board text too long to fit: '+str(text)[:30])
    return ''.join(f'<text x="{x}" y="{y+i*size*1.4:g}" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(line)}</text>' for i,line in enumerate(lines))


def render_cover_svg(body, theme):
    meta, layout = body['meta'], theme['layout']
    bg, ink, primary = theme['canvas'], theme['ink'], theme['primary']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">',
             f'<rect width="1600" height="900" fill="{bg}"/>']
    def rect(x,y,w,h,color):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')
    def line(x,y,x2,y2,color,width=2):
        parts.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')
    title_y, title_color = 260, ink
    if layout == 'editorial':
        line(80,150,170,150,primary,3)
        rect(1240,72,280,460,theme['surface'])
        title_y = 282
    elif layout == 'ledger':
        for y in range(180,560,32):
            line(80,y,1520,y,theme['hairline'],1)
        rect(80,68,1440,80,theme['secondary'])
        parts.append(_text('REGISTER  /  01',110,122,28,'#ffffff',35,1,600))
        line(230,180,230,580,theme['hairline'])
        parts.append(_text('§01',80,350,46,primary,4,1,700))
        title_y=268
    elif layout == 'nocturne':
        for x in range(80,1540,80):
            line(x,180,x,560,theme['hairline'],1)
        parts.extend([f'<circle cx="1400" cy="125" r="23" fill="{primary}"/>',
                      f'<circle cx="1400" cy="125" r="37" fill="none" stroke="{primary}" stroke-width="2"/>'])
        title_y=285
    elif layout == 'press':
        line(80,152,1520,152,ink,7)
        line(80,167,1520,167,ink,2)
        rect(80,183,180,10,primary)
        title_y=302
    elif layout == 'ink':
        parts.append(f'<ellipse cx="650" cy="332" rx="590" ry="205" fill="{ink}"/>')
        title_color=bg
        rect(1435,465,80,80,theme['secondary'])
        parts.append(_text('议',1452,521,43,bg,1,1,600))
        title_y=302
    elif layout == 'festival':
        rect(0,0,1600,570,primary)
        title_color='#140f14'
        title_y=262
        for i in range(24):
            h=20+(i*17%60)
            rect(80+i*60,565-h,36,h,theme['secondary'] if i%3==0 else '#140f14')
    left = 280 if layout=='ledger' else (240 if layout=='ink' else 80)
    if layout!='ledger':
        parts.append(_text(meta.get('eyebrow',theme['name']),80,118,28,title_color if layout=='festival' else theme['muted'],45,1,600))
    parts.append(_text(meta['title'],left,title_y,66,title_color,14 if layout=='ink' else (18 if layout=='editorial' else 20),2,700))
    if meta.get('subtitle'):
        parts.append(_text(meta['subtitle'],left,430 if layout=='ink' else (435 if layout=='festival' else 462),28,title_color if layout in ('ink','festival') else theme['muted'],29 if layout=='ink' else 36,2))
    line(80,600,1520,600,theme['hairline'],2)
    metrics=next((s['items'] for s in body['sections'] if s['type']=='metrics'), [])
    for i,item in enumerate(metrics[:3]):
        x=80+i*490
        parts.append(_text(item['value'],x,704,68,theme['secondary'] if layout=='festival' and i==0 else ink,7,1,700))
        parts.append(_text(item['label'],x,754,28,ink,14,1,600))
        parts.append(_text(item['note'],x,800,24,theme['muted'],18,2))
    if not metrics:
        parts.append(_text(meta.get('status','待讨论'),80,708,42,ink,28,1,600))
        parts.append(_text(' · '.join(meta.get('audience',[])),80,776,28,theme['muted'],45,1))
    line(80,860,1520,860,theme['hairline'],1)
    parts.append('</svg>')
    return ''.join(parts)
