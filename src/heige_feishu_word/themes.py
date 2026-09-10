"""Document color systems adapted from HeiGe-Design (MIT).

White is the shared host surface. Saturated accents, paired tints, and explicit
native color names keep SVG, HTML, and native Docx in the same color family.
"""
from copy import deepcopy


def _theme(slug, name, layout, palette, tints, secondary, native,
           native_secondary, native_accents, description, display):
    return dict(slug=slug, name=name, layout=layout, canvas="#ffffff",
                surface=tints[0], ink="#202B3D", muted="#566172",
                hairline="#DFE5EE", primary=palette[0], secondary=secondary,
                palette=palette, tints=tints, native=native,
                native_secondary=native_secondary, native_accents=native_accents,
                description=description, display=display)


# Accent roles are categorical. Only explicit callout/timeline status fields
# carry success, warning, or risk meanings. A color alone never implies a KPI trend.
THEMES = {
    'atelier-bone': _theme('atelier-bone', '海蓝鎏金简报', 'editorial',
        ['#19466A', '#97600B', '#08756A', '#AC345C', '#6848A0', '#854C32', '#60691E', '#3155A6'],
        ['#EAF2FF', '#FFF0C9', '#E5F5EE', '#FCE9F0', '#F0EAFB', '#FBEEE4', '#F0F3DA', '#E8EEFF'],
        '#D7A236', 'blue', 'orange', ['blue', 'orange', 'green', 'purple'],
        '海军蓝主读数与香槟金辅助，配松石绿和莓红，适合预算与决策。', 'sans'),
    'grid-bureau': _theme('grid-bureau', '蓝橙经营复盘', 'ledger',
        ['#2454CE', '#B4480B', '#08756A', '#7143AD', '#B62C4A', '#4147A5', '#667017', '#855041'],
        ['#EAF0FF', '#FFEFD9', '#E3F5EE', '#F1E8FC', '#FCE8EE', '#ECEBFF', '#F0F4D7', '#F9EBE5'],
        '#E57526', 'blue', 'orange', ['blue', 'orange', 'green', 'purple'],
        '钴蓝与橘色比较实际和目标，青绿与紫色区分渠道，强化数据辨识。', 'sans'),
    'nocturne-teal': _theme('nocturne-teal', '孔雀琥珀简报', 'nocturne',
        ['#006F6B', '#995A05', '#2C55B5', '#AF3164', '#347434', '#7143AD', '#A23B24', '#4F5C8C'],
        ['#DDF5EE', '#FFF0C4', '#E8EFFF', '#FCE8F0', '#E8F5DE', '#F0E8FC', '#FFEAE1', '#EBEEF9'],
        '#D99415', 'green', 'orange', ['green', 'orange', 'blue', 'purple'],
        '孔雀青搭配琥珀黄、宝蓝和莓色，将项目阶段与读数分层。', 'sans'),
    'broadsheet': _theme('broadsheet', '莓果研究速递', 'press',
        ['#B32362', '#493FB3', '#1A629F', '#16755A', '#A6530B', '#804496', '#AB3B35', '#586C24'],
        ['#FDE7F0', '#EDEAFF', '#E5F1FF', '#E3F6EB', '#FFF0D9', '#F6E9FA', '#FFEAE7', '#EDF3DA'],
        '#5950C8', 'red', 'purple', ['red', 'purple', 'blue', 'green'],
        '莓红与靛蓝交替组织证据，辅以湖蓝与翡翠绿，形成清晰的研究层次。', 'serif'),
    'moxi-void': _theme('moxi-void', '朱砂石青备忘', 'ink',
        ['#B5342C', '#176C83', '#5C6D24', '#9C590E', '#77449E', '#246455', '#A3326C', '#3656A0'],
        ['#FFE8E1', '#DFF2F6', '#EDF3D7', '#FFF0D4', '#F3E8FB', '#E1F3E9', '#FBE7F2', '#E8EFFF'],
        '#238FA1', 'red', 'blue', ['red', 'blue', 'green', 'orange'],
        '朱砂与石青形成方案对照，竹青和赭金补充条件与行动。', 'serif'),
    'soundwave-wrapped': _theme('soundwave-wrapped', '洋红明黄提案', 'festival',
        ['#B81769', '#855D00', '#3452C4', '#08756A', '#B53B24', '#7143AD', '#236F35', '#A33884'],
        ['#FFE5F1', '#FFEDA0', '#E8EDFF', '#DFF5EC', '#FFE9DD', '#F2E6FF', '#E5F5DC', '#FBE8F6'],
        '#F3CC32', 'purple', 'blue', ['purple', 'blue', 'orange', 'green'],
        '洋红主读数、明黄浅色面与宝蓝辅助，呈现发布节奏和转化层次。', 'sans'),
    'editorial-forest': _theme('editorial-forest', '森林编辑部', 'editorial',
        ['#356342', '#935715', '#315E8C', '#8B3F65', '#5E4A92', '#686521', '#256D69', '#994830'],
        ['#EAF3E6', '#FFF0DA', '#EAF1FA', '#F9EAF2', '#EEEAF7', '#F2F2DC', '#E4F4EF', '#FBEDE5'],
        '#BC862E', 'green', 'orange', ['green', 'orange', 'blue', 'purple'],
        '白页上的森林绿、麦金、湖蓝与浆果，兼容原有主题标识。', 'serif'),
}


def get_theme(slug=None):
    key = slug or "editorial-forest"
    if key not in THEMES:
        raise ValueError("unsupported theme: %r; choose %s" % (key, ", ".join(THEMES)))
    return deepcopy(THEMES[key])


def list_themes():
    return [{key: value[key] for key in ("slug", "name", "description")}
            for value in THEMES.values()]
