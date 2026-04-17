import tkinter.ttk as ttk

# ══════════════════════════════════════════════════════════════════════════════
#  PALETA
# ══════════════════════════════════════════════════════════════════════════════
BG_DARK   = "#2C1407"
BG_MID    = "#61250F"
BG_PANEL  = "#441603"
BG_INPUT  = "#2E1E13"
ACCENT    = "#ffbb7b"
ACCENT2   = "#e68d4e"
ACCENT3   = "#a0f099"
ACCENT4   = "#79be8e"
ACCENT5   = "#46b520"
ACCENT6   = "#000000"
TEXT_MAIN = "#d1e4bf"
TEXT_DIM  = "#ffbe9e"
BORDER    = "#d4ed8b"

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