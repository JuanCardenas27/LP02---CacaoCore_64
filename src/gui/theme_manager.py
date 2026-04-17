PALETTES = {
    "current": {
        "BG_DARK": "#2C1407",
        "BG_MID": "#61250F",
        "BG_PANEL": "#441603",
        "BG_INPUT": "#2E1E13",
        "ACCENT": "#ffbb7b",
        "ACCENT2": "#e68d4e",
        "ACCENT3": "#a0f099",
        "ACCENT4": "#79be8e",
        "ACCENT5": "#46b520",
        "ACCENT6": "#000000",
        "TEXT_MAIN": "#d1e4bf",
        "TEXT_DIM": "#ffbe9e",
        "BORDER": "#d4ed8b",
    },
    "legacy": {
        "BG_DARK": "#0D0F12",
        "BG_MID": "#141720",
        "BG_PANEL": "#1A1D28",
        "BG_INPUT": "#0A0C10",
        "ACCENT": "#00FF9C",
        "ACCENT2": "#00C8FF",
        "ACCENT3": "#FF6B6B",
        "ACCENT4": "#FFD166",
        "ACCENT5": "#C3A6FF",
        "ACCENT6": "#000000",
        "TEXT_MAIN": "#E0E8F0",
        "TEXT_DIM": "#5A6880",
        "BORDER": "#5C6FB3",
    },
}

PALETTE_KEYS = tuple(PALETTES["current"].keys())
STYLE_WIDGET_KEYS = (
    "bg",
    "background",
    "fg",
    "foreground",
    "activebackground",
    "activeforeground",
    "highlightbackground",
    "highlightcolor",
    "selectbackground",
    "selectforeground",
    "insertbackground",
    "troughcolor",
    "bordercolor",
)


def get_palette(name):
    return PALETTES.get(name, PALETTES["current"])


def apply_palette_namespace(namespace, name):
    palette = get_palette(name)
    for key in PALETTE_KEYS:
        namespace[key] = palette[key]


def _remap_value(value, source_palette, target_palette):
    for key in PALETTE_KEYS:
        if value == source_palette[key]:
            return target_palette[key]
    return value


def recolor_widget_tree(widget, name):
    target_palette = get_palette(name)
    source_name = "legacy" if name == "current" else "current"
    source_palette = get_palette(source_name)

    try:
        widget_keys = set(widget.keys())
    except Exception:
        widget_keys = set()

    updates = {}
    for key in STYLE_WIDGET_KEYS:
        if key in widget_keys:
            try:
                current_value = widget.cget(key)
            except Exception:
                continue
            remapped = _remap_value(current_value, source_palette, target_palette)
            if remapped != current_value:
                updates[key] = remapped

    if updates:
        try:
            widget.configure(**updates)
        except Exception:
            pass

    for child in widget.winfo_children():
        recolor_widget_tree(child, name)
