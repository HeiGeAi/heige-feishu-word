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


# Feishu documents have a white reading surface. These are document adaptations
# of the original design systems, not reproductions of their standalone pages.
THEMES = {
    "atelier-bone": _theme("atelier-bone", "白金管理简报", "editorial",
        ("#ffffff", "#faf9f6", "#252a34", "#68707c", "#e6e8ed", "#8b6d37", "#65563e"),
        "orange", "白纸、细金线、克制留白。先呈现判断，再展开证据。", "sans"),
    "grid-bureau": _theme("grid-bureau", "蓝图经营复盘", "ledger",
        ("#ffffff", "#f7f9fc", "#242b37", "#647084", "#e6eaf0", "#2757d6", "#516b9b"),
        "blue", "白色记录页、蓝色读数、精确对齐，适合周期复盘。", "sans"),
    "nocturne-teal": _theme("nocturne-teal", "青岚项目简报", "nocturne",
        ("#ffffff", "#f6faf9", "#263438", "#65777b", "#e2eae8", "#087f73", "#4b9188"),
        "green", "白页、电青收敛为深青，细线组织进度与风险。", "sans"),
    "broadsheet": _theme("broadsheet", "知见研究速递", "press",
        ("#ffffff", "#faf8f6", "#2c2b29", "#716d67", "#e8e4df", "#a74032", "#77665a"),
        "red", "白色报页、细双线、小面积砖红，证据优先。", "serif"),
    "moxi-void": _theme("moxi-void", "朱墨决策备忘", "ink",
        ("#ffffff", "#faf9f7", "#30302e", "#72716d", "#e5e4e1", "#494944", "#b34b3f"),
        "gray", "白纸深墨、朱砂小印、同口径比较，留白服务阅读。", "serif"),
    "soundwave-wrapped": _theme("soundwave-wrapped", "玫红发布提案", "festival",
        ("#ffffff", "#fcf8fa", "#332b32", "#786b77", "#ece4e9", "#b52664", "#80647d"),
        "purple", "白页与少量玫红标记，声浪缩为短线，突出发布重点。", "sans"),
    "editorial-forest": _theme("editorial-forest", "森林编辑部", "editorial",
        ("#ffffff", "#f7f9f5", "#2d3a30", "#667366", "#e3e8df", "#43684b", "#866e57"),
        "green", "兼容原有主题标识，使用白页与森林绿。", "serif"),
}

_DATA_PALETTES = {
    "atelier-bone": ["#8b6d37", "#738799", "#6e8191", "#c1ac88", "#758579", "#a88879", "#8c8997", "#afb4ad"],
    "grid-bureau": ["#2757d6", "#6f8dad", "#536b8e", "#869ea7", "#8c96ba", "#657a91", "#b4becb", "#777f99"],
    "nocturne-teal": ["#087f73", "#608f85", "#527e89", "#88a8b8", "#668f7c", "#abbcad", "#627593", "#839bab"],
    "broadsheet": ["#a74032", "#9c7e66", "#7b8b95", "#a78b81", "#8e967e", "#a797b1", "#687683", "#b5b3a3"],
    "moxi-void": ["#494944", "#808078", "#7c8883", "#a99b8e", "#727c89", "#b9b9b1", "#8c8a80", "#a5b2ab"],
    "soundwave-wrapped": ["#b52664", "#b36e8b", "#8d829d", "#c0b4ce", "#927d85", "#bf909a", "#899ca8", "#a1ada7"],
    "editorial-forest": ["#43684b", "#a2b59b", "#718680", "#ac957e", "#73849b", "#9d9296", "#9eaa91", "#747e70"],
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
