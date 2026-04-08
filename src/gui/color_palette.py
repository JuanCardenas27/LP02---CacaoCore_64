import tkinter.ttk as ttk

# ══════════════════════════════════════════════════════════════════════════════
#  PALETA
# ══════════════════════════════════════════════════════════════════════════════
BG_DARK   = "#0D0F12"
BG_MID    = "#141720"
BG_PANEL  = "#1A1D28"
BG_INPUT  = "#0A0C10"
ACCENT    = "#00FF9C"
ACCENT2   = "#00C8FF"
ACCENT3   = "#FF6B6B"
ACCENT4   = "#FFD166"
ACCENT5   = "#C3A6FF"
TEXT_MAIN = "#E0E8F0"
TEXT_DIM  = "#5A6880"
BORDER    = "#5C6FB3"

FM       = ("Courier New", 11)
FM_SM    = ("Courier New",  9)
FM_LG    = ("Courier New", 14, "bold")
FM_XL    = ("Courier New", 20, "bold")
FM_TITLE = ("Courier New", 20, "bold")
FM_LABEL = ("Courier New", 10)
FM_BTN   = ("Courier New", 11, "bold")
FM_BTN_1   = ("Courier New", 12, "bold")
FM_BTN_CMP   = ("Courier New", 15, "bold")

# ══════════════════════════════════════════════════════════════════════════════
#  ESTILOS
# ══════════════════════════════════════════════════════════════════════════════
def setup_styles():
    style = ttk.Style()

    style.theme_use("clam")

    style.configure(
        "SymbolTable.Treeview",
        background=BG_INPUT,
        foreground=TEXT_MAIN,
        fieldbackground=BG_INPUT,
        bordercolor=BG_INPUT,
        rowheight=25,
        font=FM
    )

    style.configure(
        "SymbolTable.Treeview.Heading",
        background=BG_PANEL,
        foreground=ACCENT4,
        font=FM_BTN,
        relief="flat"
    )

    style.map(
        "SymbolTable.Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", BG_PANEL)]
    )