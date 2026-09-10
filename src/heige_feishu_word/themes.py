"""Portable visual tokens, adapted from HeiGe-Design (MIT).

Native Docx uses named colors and its own fonts. Exact tokens apply to SVG and
HTML; the mapping is explicit rather than promising CSS styling of native blocks.
"""

from copy import deepcopy


def _theme(slug, name, layout, colors, native, description, display):
    canvas, surface, ink, muted, hairline, primary, secondary = colors
    return dict(slug=slug, name=name, layout=layout, canvas=canvas,
                surface=surface, ink=ink, muted=muted, hairline=hairline,
                primary=primary, secondary=secondary,
                palette=[primary, ink, muted, secondary, hairline],
                native=native, description=description, display=display)


THEMES = {
    "atelier-bone": _theme("atelier-bone", "象牙管理简报", "editorial",
        ("#f3ede1", "#faf6ec", "#33302b", "#6b655c", "#d9cfbd", "#a98b4e", "#221e18"),
        "orange", "象牙纸、金线起笔、大数字与疏朗节奏。适合管理层简报。", "serif"),
    "grid-bureau": _theme("grid-bureau", "瑞士经营看板", "ledger",
        ("#f4f5f7", "#ffffff", "#1a1d24", "#5b6270", "#d5d8dd", "#2757d6", "#14171d"),
        "blue", "编号侧栏、等宽读数、严整基线。适合经营数据与周报。", "sans"),
    "nocturne-teal": _theme("nocturne-teal", "深空项目战报", "nocturne",
        ("#08090d", "#0f1319", "#e9edf3", "#8a94a4", "#20262f", "#2dd4bf", "#5ff0dc"),
        "green", "深空底、电青焦点、状态灯。适合项目进展与技术复盘。", "sans"),
    "broadsheet": _theme("broadsheet", "大报研究速递", "press",
        ("#f4f1ea", "#ece6d8", "#1c1a16", "#5c554a", "#cdc6b8", "#c0392b", "#1c1a16"),
        "red", "报头双线、衬线标题、证据分栏。适合洞察与研究报告。", "serif"),
    "moxi-void": _theme("moxi-void", "水墨决策备忘", "ink",
        ("#f4f0e6", "#fbf8f0", "#1c1a17", "#6b655c", "#d9d2c2", "#1c1a17", "#c8483a"),
        "gray", "松烟墨、朱砂落款、宽留白。适合战略思考与方案评审。", "serif"),
    "soundwave-wrapped": _theme("soundwave-wrapped", "声浪发布提案", "festival",
        ("#0e0c14", "#1b1826", "#f7f4ec", "#ada8bc", "#2e2b3c", "#ff2d95", "#ffe500"),
        "purple", "粉色宣告、电黄高光、波形节奏。适合发布和活动复盘。", "sans"),
    "editorial-forest": _theme("editorial-forest", "森林编辑部", "editorial",
        ("#efe7d4", "#ffffff", "#2e4a2a", "#53604f", "#c6ccb8", "#2e4a2a", "#e89cb1"),
        "green", "兼容原有森林样式，扩展完整图表和正文。", "serif"),
}

# Data marks need separation from the canvas. Hairline is never a data color.
# Numbered labels remain present so color is never the sole identifier.
_DATA_PALETTES = {
    "atelier-bone": ["#a98b4e", "#33302b", "#6b655c", "#8f7550", "#535c52", "#927264", "#706853", "#7b7b70"],
    "grid-bureau": ["#2757d6", "#1a1d24", "#5b6270", "#3a67ad", "#7889a2", "#365072", "#737980", "#516bb5"],
    "nocturne-teal": ["#2dd4bf", "#e9edf3", "#8a94a4", "#68b6ad", "#b7ccc9", "#59a1b0", "#a1b6d0", "#6f958c"],
    "broadsheet": ["#c0392b", "#1c1a16", "#5c554a", "#9a6f59", "#7e8273", "#8c605f", "#596777", "#918061"],
    "moxi-void": ["#1c1a17", "#6b655c", "#968b77", "#4d5650", "#666f71", "#86796c", "#47443e", "#737765"],
    "soundwave-wrapped": ["#ff2d95", "#ffe500", "#91acff", "#f7f4ec", "#ada8bc", "#f69cce", "#cac26a", "#7ec9ce"],
    "editorial-forest": ["#2e4a2a", "#a34b61", "#657659", "#966940", "#586e82", "#8d716d", "#405450", "#71715c"],
}
for _slug, _colors in _DATA_PALETTES.items():
    THEMES[_slug]["palette"] = _colors


def get_theme(slug=None):
    key = slug or "editorial-forest"
    if key not in THEMES:
        raise ValueError("unsupported theme: %r; choose %s" % (key, ", ".join(THEMES)))
    return deepcopy(THEMES[key])


def list_themes():
    return [{key: value[key] for key in ("slug", "name", "description")}
            for value in THEMES.values()]
