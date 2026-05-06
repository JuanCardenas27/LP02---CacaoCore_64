"""
CACAO_Core-64 — Interfaz Gráfica Principal
==========================================
Panel de control del procesador simulado de 64 bits.
Coloca este archivo en src/ y ejecutalo con: python cacao_gui.py

Cambios respecto a la versión anterior:
  - Toda lógica de carga de archivos → RAM extraída a cacao_loader.py
  - Se importa CacaoLoaderPanel y se integra en columna C (row 2)
  - self.loader_panel disponible como atributo público
  - Importa CacaoConsole desde cacao_console.py  →  self.console
"""
# TODO: Modularizar cacao_gui.py.

import tkinter as tk
from tkinter import messagebox
import os
from time import sleep
from enlazador_cargador.loader_txt import loader_txt
from compiler.compiler_gui import CompilerGui
import compiler.compiler_gui as compiler_gui_module
from cacao_core import CacaoCore64, RUNNING
from peripherals.cacao_console import CacaoConsole
import peripherals.cacao_console as cacao_console_module
import gui.styles_console as styles_console_module
import gui.styles_cacao as styles_cacao_module
from gui.styles_cacao import *
from gui.theme_manager import apply_palette_namespace, recolor_widget_tree
from gui.zoom_manager import ZoomManager

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════════════════════════
def make_panel(parent, title, color=ACCENT2, padx=10, pady=8):
    outer = tk.Frame(parent, bg=BORDER, bd=1, relief="flat")
    tk.Label(outer, text=f" {title} ", font=FM,
             fg=BG_DARK, bg=color, anchor="w").pack(fill="x")
    inner = tk.Frame(outer, bg=BG_PANEL, padx=padx, pady=pady)
    inner.pack(fill="both", expand=True)
    return outer, inner

def make_button(parent, text, color, command):
    btn = tk.Button(parent, text=text, font=FM_BTN,
                    bg=BG_MID, fg=color,
                    activebackground=color, activeforeground=BG_DARK,
                    relief="flat", bd=0, pady=8, cursor="hand2",
                    command=command)
    btn.bind("<Enter>", lambda e: btn.config(bg=color, fg=BG_DARK))
    btn.bind("<Leave>", lambda e: btn.config(bg=BG_MID, fg=color))
    return btn

def make_vert_scrollable(parent):
    canvas = tk.Canvas(parent, bg=BG_PANEL, highlightthickness=0 )
    sb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)

    sb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    sf = tk.Frame(canvas, bg=BG_PANEL)

    win_id = canvas.create_window((0, 0), window=sf, anchor="nw")
    sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    return sf

def make_hor_scrollable(parent):
    canvas = tk.Canvas(parent, bg=BG_PANEL, highlightthickness=0, height=100) # Altura fija para flags
    sb = tk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
    canvas.configure(xscrollcommand=sb.set)

    sb.pack(side="bottom", fill="x")
    canvas.pack(side="top", fill="both", expand=True)

    sf = tk.Frame(canvas, bg=BG_PANEL)
    win_id = canvas.create_window((0, 0), window=sf, anchor="nw")

    sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    #canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
    
    def _on_mousewheel_h(event):
        canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel_h))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    return sf
    

# ══════════════════════════════════════════════════════════════════════════════
#  VENTANA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class CacaoCoreGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self._core = CacaoCore64()
        self._fmt  = tk.StringVar(value="hex")
        self._reg_labels   = {}
        self._flag_widgets_alu = {}
        self._flag_widgets_fau = {}
        self._format_rbs = []
        self._palette_name = "current"

        # Atributos públicos de componentes externos
        self.console      = None   # CacaoConsole       — asignado en _build_console_panel
        self.loader_panel = None   # CacaoLoaderPanel   — asignado en _build_loader_panel

        self.title("CACAO_Core-64  ·  Panel de Control")
        self.configure(bg=BG_DARK)
        self.minsize(1280, 700)
        self.resizable(True, True)
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-zoomed", True)

        self._build_header()
        self._build_body()
        self._build_statusbar()

        self._zoom_manager = ZoomManager(
            self,
            font_base=FM,
            font_lg=FM_LG,
            font_xl=FM_XL,
            font_title=FM_TITLE,
            font_subtitle=("Courier New", 14),
            font_sm=FM_SM,
            font_btn=FM_BTN,
            font_label=FM_LABEL,
            bg_panel=BG_PANEL,
            bg_mid=BG_MID,
            bg_dark=BG_DARK,
            text_main=TEXT_MAIN,
            accent=ACCENT,
            accent2=ACCENT2,
            accent4=ACCENT4,
            min_layout_zoom=0.1,
            on_palette_change=self._apply_palette,
            initial_palette=self._palette_name,
        )
        self._zoom_manager.attach_widgets(
            header_title=self._hdr_title,
            header_subtitle=self._hdr_subtitle,
            header_info=self._hdr_info,
            settings_button=self._settings_btn,
            status_label=self._status_lbl,
            reg_labels=self._reg_labels,
            flag_widgets_alu=self._flag_widgets_alu,
            flag_widgets_fau=self._flag_widgets_fau,
            format_rbs=self._format_rbs,
        )
        self._zoom_manager.initialize()

        self.after(100, self._refresh_registers)
        
        self._core.processor.io_controller.console = self.console

    # ─────────────────────────────────────────────────────────────────────
    #  HEADER
    # ─────────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_DARK, pady=10)
        hdr.pack(fill="x", padx=18, side="top")

        self.icono = tk.PhotoImage(file=r"src\gui\assets\Cacao_logo.png").subsample(10)
        tk.Label(hdr, image=self.icono, width=40, height=40,
                 bg=BG_DARK).pack(side="left", padx=(0, 10))

        self._hdr_title = tk.Label(
            hdr,
            text="CACAO_Core-64",
            font=FM_TITLE,
            fg=ACCENT,
            bg=BG_DARK,
        )
        self._hdr_title.pack(side="left")

        self._hdr_subtitle = tk.Label(
            hdr,
            text="   PANEL DE CONTROL",
            font=("Courier New", 14),
            fg=ACCENT2,
            bg=BG_DARK,
        )
        self._hdr_subtitle.pack(side="left")

        tk.Frame(hdr, bg=BG_DARK).pack(side="left", fill="x", expand=True)

        self._settings_btn = tk.Button(
            hdr,
            text="⚙️ Configurar",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT4,
            activebackground=ACCENT4,
            activeforeground=BG_DARK,
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._toggle_settings_popup,
        )
        self._settings_btn.pack(side="left", padx=(20, 20))

        self._hdr_info = tk.Label(
            hdr,
            text="64-bit  ·  Von Neumann  ·  1 MB RAM   |   cacao_core.py",
            font=FM,
            fg=TEXT_DIM,
            bg=BG_DARK,
        )
        self._hdr_info.pack(side="left")

        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x", padx=18, side="top")

    # ─────────────────────────────────────────────────────────────────────
    #  BODY
    # ─────────────────────────────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=18, pady=10, side="top")

        body.columnconfigure(0, weight=1, uniform="col")
        body.columnconfigure(1, weight=1, uniform="col")
        body.columnconfigure(2, weight=1, uniform="col")
        body.columnconfigure(3, weight=1, uniform="col")
        body.rowconfigure(0, weight=1)

        col_a = tk.Frame(body, bg=BG_DARK)
        col_a.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        col_b = tk.Frame(body, bg=BG_DARK)
        col_b.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

        col_c = tk.Frame(body, bg=BG_DARK)
        col_c.grid(row=0, column=2, columnspan=2, sticky="nsew")

        # ── Columna A ─────────────────────────────────────────────────────
        col_a.rowconfigure(0, weight=0)
        col_a.rowconfigure(1, weight=0)
        col_a.rowconfigure(2, weight=3)
        col_a.rowconfigure(3, weight=2)

        col_a.columnconfigure(0, weight=1)
        
        ctrl_frame = tk.Frame(col_a, bg=BG_DARK)
        ctrl_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self._build_control_panel(ctrl_frame)

        spl_frame = tk.Frame(col_a, bg=BG_DARK)
        spl_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self._build_spl_button(spl_frame)

        self._build_alu_flags_panel(col_a)

        self._build_fau_flags_panel(col_a)


        # ── Columna B ─────────────────────────────────────────────────────
        col_b.rowconfigure(0, weight=0)
        col_b.rowconfigure(1, weight=0)
        col_b.rowconfigure(2, weight=1)
        col_b.rowconfigure(3, weight=3)
        col_b.columnconfigure(0, weight=1)

        self._build_pc_ir_panel(col_b)

        sregs_frame = tk.Frame(col_b, bg=BG_DARK)
        sregs_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 6))
        self._build_special_regs_panel(sregs_frame)

        gpr_frame = tk.Frame(col_b, bg=BG_DARK)
        gpr_frame.grid(row=3, column=0, sticky="nsew")
        self._build_gpr_panel(gpr_frame)

        # ── Columna C ─────────────────────────────────────────────────────
        col_c.rowconfigure(0, weight=1)
        col_c.rowconfigure(1, weight=2)

        col_c.columnconfigure(0, weight=1)

        self._build_console_panel(col_c)
        self._build_ram_panel(col_c)
        


    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA A: CONTROL
    # ─────────────────────────────────────────────────────────────────────
    def _build_control_panel(self, parent):
        outer, pf = make_panel(parent, "⚙  CONTROL DE EJECUCIÓN", ACCENT)
        outer.pack(fill="x")

        sa_row = tk.Frame(pf, bg=BG_PANEL)
        sa_row.pack(fill="x", pady=(0, 8))

        tk.Label(sa_row, text="Start Address:", font=FM_LABEL,
                 fg=ACCENT4, bg=BG_PANEL).pack(side="left")
        tk.Label(sa_row, text="0x", font=FM, fg=TEXT_DIM,
                 bg=BG_PANEL).pack(side="left")

        self._start_addr_var = tk.StringVar(value="00001000")
        tk.Entry(sa_row, textvariable=self._start_addr_var,
                 font=FM, bg=BG_INPUT, fg=ACCENT4,
                 insertbackground=ACCENT, relief="flat",
                 width=8, bd=4,
                 highlightthickness=1,
                 highlightcolor=ACCENT2,
                 highlightbackground=BORDER
                 ).pack(side="left", padx=2)
        
        row = tk.Frame(pf, bg=BG_PANEL)
        row.pack(fill="x")

        for val, lbl, color in [("hex","HEX",ACCENT5), ("dec","DEC",ACCENT)]:
            rb = tk.Radiobutton(
                sa_row, text=lbl, variable=self._fmt, value=val,
                font=FM_SM, fg=ACCENT6, bg=BG_MID,
                selectcolor=color,
                activebackground=BG_MID, activeforeground=color,
                indicatoron=False, width=3, pady=6, relief="flat",
                cursor="hand2", command=self._refresh_registers
            )
            rb.pack(side="right", padx=3)
            self._format_rbs.append(rb)

        tk.Frame(pf, bg=BORDER, height=1).pack(fill="x", pady=(0, 6))

        for label, color, cmd in [
            ("⚡  BOOT",       ACCENT,  self._do_boot),
            ("▶|  RUN STEP",  ACCENT2, self._do_run_step),
        ]:
            make_button(pf, label, color, cmd).pack(fill="x", pady=3)
        
        run_full_row = tk.Frame(pf, bg=BG_PANEL)
        run_full_row.pack(fill="x", pady=3)

        make_button(run_full_row, "▶▶  RUN FULL", ACCENT5, self._do_run_full).pack(side="left", fill="x", expand=True)

        # Sub-frame compacto para input y label
        self._intertime = tk.StringVar(value="0")
        time_frame = tk.Frame(run_full_row, bg=BG_INPUT, relief="flat", bd=4,
                              highlightthickness=1, highlightcolor=ACCENT2,
                              highlightbackground=BORDER)
        time_frame.pack(side="left", padx=(8, 0), fill="y")
        
        tk.Entry(time_frame, textvariable=self._intertime,
                 font=FM, bg=BG_INPUT, fg=ACCENT2,
                 insertbackground=ACCENT, relief="flat", bd=0,
                 width=8).pack(side="left", padx=4, pady=4)
        
        tk.Label(time_frame, text="seg", font=FM, fg=ACCENT2,
                 bg=BG_INPUT).pack(side="left", padx=(0, 4), pady=4)
        
    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA A: SPL_BUTTON
    # ─────────────────────────────────────────────────────────────────────
    def _build_spl_button(self, parent):
        outer, pf = make_panel(parent, "SISTEMA DE PROC. DE LENGUAJE", ACCENT2)
        outer.pack(fill="x")

        sa_row = tk.Frame(pf, bg=BG_PANEL)
        sa_row.pack(fill="x")

        compile_button = tk.Button(sa_row, text="Compilar y Cargar", bg = ACCENT, anchor="center",
                                   font = FM_BTN_CMP, command=self._open_compiler)
        compile_button.pack(fill="x", padx=8, pady=6)
        
    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA A: FLAGS ALU
    # ─────────────────────────────────────────────────────────────────────
    def _build_alu_flags_panel(self, parent):
        # PARA ALU
        outer, pf = make_panel(parent,
                               "⚑  FLAGS REGISTER  [ ALU ]",
                               ACCENT3)
        outer.grid(row=2, column=0, sticky="nsew", pady=(0, 6))

        sf = make_hor_scrollable(pf)


        FLAG_DEFS = [
            (5, "DZ", "DivZero", ACCENT5),
            (4, "Z", "Zero",      ACCENT),
            (3, "N", "Negative",  ACCENT3),
            (2, "C", "Carry",     ACCENT2),
            (1, "V", "Overflow",  ACCENT4),
            (0, "I", "Interrupt", ACCENT5),
        ]

        for bit_idx, short, desc, color in FLAG_DEFS:
            col = tk.Frame(sf, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
            col.pack(side="left", padx=0, pady=1)
            
            tk.Label(col, text=short, font=FM_LG, width=6,
                    fg=color, bg=BG_PANEL).pack(pady=(1,1))
            
            tk.Label(col, text=desc, font=FM_SM,
                    fg=TEXT_DIM, bg=BG_PANEL).pack(padx=10)
            
            ind = tk.Label(col, text="0", font=FM,
                        fg=TEXT_DIM, bg=BG_MID, pady=0)
            ind.pack(pady=(1,1), fill="x")
        
            self._flag_widgets_alu[bit_idx] = (ind, color)

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA A: FLAGS FAU
    # ─────────────────────────────────────────────────────────────────────

    def _build_fau_flags_panel(self, parent):
        outer, pf = make_panel(parent,
                               "⚑  FLAGS REGISTER  [ FAU ]",
                               ACCENT5)
        outer.grid(row=3, column=0, sticky="nsew", pady=(0, 6))

        sf = make_hor_scrollable(pf)


        FLAG_DEFS = [
            (2, "IX", "Inexact",  ACCENT2),
            (1, "IO", "InvalidOp",  ACCENT4),
            (0, "UF", "Underflow", ACCENT5),
        ]

        for bit_idx, short, desc, color in FLAG_DEFS:
            col = tk.Frame(sf, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
            col.pack(side="left", padx=0, pady=1)
            
            tk.Label(col, text=short, font=FM_LG, width=6,
                    fg=color, bg=BG_PANEL).pack(pady=(1,1))
            
            tk.Label(col, text=desc, font=FM_SM,
                    fg=TEXT_DIM, bg=BG_PANEL).pack(padx=10)
            
            ind = tk.Label(col, text="0", font=FM,
                        fg=TEXT_DIM, bg=BG_MID, pady=0)
            ind.pack(pady=(1,1), fill="x")
        
            self._flag_widgets_fau[bit_idx] = (ind, color)

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA B: PC y IR
    # ─────────────────────────────────────────────────────────────────────
    def _build_pc_ir_panel(self, parent):
        for row_idx, (name, title, color) in enumerate([
            ("pc", "▸  PROGRAM COUNTER  [ PC ]", ACCENT),
            ("ir", "▸  INSTRUCTION REG  [ IR ]", ACCENT2),
        ]):
            outer, pf = make_panel(parent, title, color, padx=8, pady=6)
            outer.grid(row=row_idx, column=0, sticky="ew", pady=(0, 6))
            lbl = tk.Label(pf, text="0x0000000000000000",
                           font=FM_XL, fg=color, bg=BG_PANEL, anchor="center")
            lbl.pack(fill="x", pady=6)
            self._reg_labels[name] = lbl

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA B: SPECIAL REGISTERS
    # ─────────────────────────────────────────────────────────────────────
    def _build_special_regs_panel(self, parent):
        outer, pf = make_panel(parent, "◉  REGISTROS ESPECIALES", ACCENT3, padx=6, pady=4)
        outer.pack(fill="both", expand=False)
        pf.pack_configure(fill="both", expand=False)

        canvas = tk.Canvas(pf, bg=BG_PANEL, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        sf = make_vert_scrollable(canvas)

        for name, lbl_txt, color in [("sp",  "$sp   Stack Pointer", ACCENT4),
            ("lr",  "$lr   Link Register", ACCENT2),
            ("acc", "$acc  Acumulador",    ACCENT),
            ("mar", "MAR", ACCENT4),
            ("mdr", "MDR", ACCENT5),
            ("dp",  "DP", TEXT_DIM),
            ("aflg","flags - ALU", ACCENT3),
            ("fflg","flags - FAU", ACCENT2)]:
            row = tk.Frame(sf, bg=BG_PANEL)
            row.pack(fill="x", padx=2, pady=1)
            tk.Label(row, text=lbl_txt, font=FM, fg=color,
                     bg=BG_PANEL, width=20, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="—", font=FM, fg=TEXT_MAIN,
                           bg=BG_INPUT, anchor="e", padx=6)
            lbl.pack(side="left", fill="x", expand=True)
            self._reg_labels[name] = lbl

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA B: REGISTERS
    # ─────────────────────────────────────────────────────────────────────
    
    def _build_gpr_panel(self, parent):
        outer, pf = make_panel(parent, "█  REGISTROS GPR  (r0 – r12)", ACCENT5, padx=6, pady=4)
        outer.pack(fill="both", expand=True)
        pf.pack_configure(fill="both", expand=True)

        canvas = tk.Canvas(pf, bg=BG_PANEL, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        sf = make_vert_scrollable(canvas)

        for i in range(13):
            name = f"r{i}"
            row = tk.Frame(sf, bg=BG_PANEL)
            row.pack(fill="x", padx=2, pady=1)
            tk.Label(row, text=f"${name:<4}", font=FM, fg=ACCENT2,
                     bg=BG_PANEL, width=6, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="0x0000000000000000",
                           font=FM, fg=TEXT_MAIN, bg=BG_INPUT,
                           anchor="e", relief="flat", padx=4)
            lbl.pack(side="left", fill="x", expand=True)
            self._reg_labels[name] = lbl

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA C — row 1: BOTÓN RAM EDITOR
    # ─────────────────────────────────────────────────────────────────────
    def _build_ram_panel(self, parent):
        outer, pf = make_panel(parent, "◈  MEMORIA RAM", ACCENT4)
        outer.grid(row=1, column=0, sticky="nsew", pady=(0, 6))

        tk.Label(pf, text=(
            "Accede al editor directo de RAM para inspeccionar,\n"
            "cargar y modificar el contenido de memoria.\n"
            "Se abre como ventana independiente."
        ), font=FM_SM, fg=TEXT_DIM, bg=BG_PANEL,
            justify="left", anchor="w").pack(fill="x", pady=(0, 14))

        btn = make_button(pf, "  ◈  ABRIR RAM EDITOR  ", ACCENT4,
                          self._open_ram_editor)
        btn.pack(anchor="w", ipadx=8, ipady=4)

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA C — row 3: CONSOLA
    # ─────────────────────────────────────────────────────────────────────
    def _build_console_panel(self, parent):
        """
        Integra CacaoConsole (de cacao_console.py) en columna C row 3.
        Disponible como self.console.

        API pública:
            self.console.write("texto")
            self.console.write_info("info")
            self.console.write_ok("ok")
            self.console.write_warn("aviso")
            self.console.write_error("error")
            self.console.write_hex("PC", 0x1000, bits=32)
            self.console.write_separator()
            self.console.clear()
            self.console.save_log()
        """
        self.console = CacaoConsole(parent, show_timestamps=True, show_toolbar=True)
        self.console.frame.grid(row=0, column=0, sticky="nsew")
        
        # Enlazar la consola al loader_panel ahora que ya existe
        if self.loader_panel is not None:
            self.loader_panel.set_console(self.console)

    # ─────────────────────────────────────────────────────────────────────
    #  STATUS BAR
    # ─────────────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")
        bar = tk.Frame(self, bg=BG_MID, pady=4)
        bar.pack(fill="x", side="bottom")
        self._status_var = tk.StringVar(value="  Sistema listo.")
        self._status_lbl = tk.Label(bar, textvariable=self._status_var,
                                    font=FM_SM, fg=ACCENT, bg=BG_MID,
                                    anchor="w", padx=12)
        self._status_lbl.pack(side="left")
        tk.Label(bar,
                 text="CACAO_Core-64  ·  Simulador Von Neumann 64-bit  ·  1 MB RAM",
                 font=FM_SM, fg=TEXT_DIM, bg=BG_MID,
                 anchor="e", padx=12).pack(side="right")

    # ─────────────────────────────────────────────────────────────────────
    #  FORMATO DE VALORES
    # ─────────────────────────────────────────────────────────────────────
    def _fmt_val(self, val, bits=64):
        val = int(val) & ((1 << bits) - 1)
        fmt = self._fmt.get()
        if fmt == "hex":
            return f"0x{val:0{bits//4}X}"
        if fmt == "dec":
            if val >= (1 << (bits - 1)):
                val -= (1 << bits)
            return str(val)
        if fmt == "bin":
            return f"0b{val:0{bits}b}"
        if fmt == "oct":
            return f"0o{val:0{(bits+2)//3}o}"
        return str(val)

    # ─────────────────────────────────────────────────────────────────────
    #  REFRESH REGISTERS
    # ─────────────────────────────────────────────────────────────────────
    def _refresh_registers(self):
        regs = self._core.processor.get_registers()
        if not regs:
            return

        for i in range(13):
            lbl = self._reg_labels.get(f"r{i}")
            if lbl:
                lbl.config(text=self._fmt_val(regs.get(f"r{i}", 0)))

        for name in ("sp", "lr", "acc"):
            lbl = self._reg_labels.get(name)
            if lbl:
                lbl.config(text=self._fmt_val(regs.get(name, 0)))

        for name in ("pc", "ir"):
            lbl = self._reg_labels.get(name)
            if lbl:
                val = int(regs.get(name, 0)) & 0xFFFFFFFFFFFFFFFF
                lbl.config(text=f"0x{val:016X}")

        for name, bits in (("mar", 32), ("mdr", 48), ("dp", 8)):
            lbl = self._reg_labels.get(name)
            if lbl:
                lbl.config(text=self._fmt_val(regs.get(name, 0), bits))
                
        for name in ("aflg", "fflg"):
            lbl = self._reg_labels.get(name)
            if lbl:
                val = int(regs.get(name, 0)) & 0xFF
                lbl.config(text=f"0x{val:02X} · 0b{val:08b}")
                widgets = self._flag_widgets_fau if name == "fflg" else self._flag_widgets_alu

            for bit_idx, (ind, color) in widgets.items():
                bit_set = bool((val >> bit_idx) & 1)
                ind.config(
                    text="1" if bit_set else "0",
                    fg=color  if bit_set else TEXT_DIM,
                    bg=BG_PANEL if bit_set else BG_MID
                )
                ind.update()

    # ─────────────────────────────────────────────────────────────────────
    #  ACCIONES DE EJECUCIÓN
    # ─────────────────────────────────────────────────────────────────────
    def _parse_addr(self):
        raw = self._start_addr_var.get().strip().lstrip("0x").lstrip("0X")
        try:
            return int(raw or "0", 16)
        except ValueError:
            messagebox.showerror("Error",
                f"Direccion invalida: '0x{raw}'\nIngresa un numero hexadecimal.")
            return None

    def _do_boot(self):
        addr = self._parse_addr()
        if addr is None:
            return
        try:
            self._core.boot(addr)
            self._refresh_registers()
            msg = f"BOOT completado  ·  PC -> 0x{addr:08X}"
            self._set_status(msg, ACCENT)
            if self.console:
                self.console.write_ok(msg)
                self.console.write_hex("PC", addr, bits=32)
            # Propagar la RAM actualizada al loader
            if self.loader_panel and hasattr(self._core, "ram"):
                self.loader_panel.set_ram(self._core.ram_memory)
        except Exception as e:
            self._set_status(f"ERROR en BOOT: {e}", ACCENT3)
            if self.console:
                self.console.write_error(f"ERROR en BOOT: {e}")
            messagebox.showerror("Error de BOOT", str(e))

    def _do_run_full(self):
        while self._core.processor.state == RUNNING:
            try:
                intertime = float(self._intertime.get())
            except Exception:
                print("[GUI - Run Full Input] ¡Error! El tiempo debe ser un número.")
            sleep(intertime)
            self._core.run_step()
            if intertime != 0:
                self._refresh_registers()
        msg = "RUN FULL completado  ·  procesador detenido (HLT)"
        self._set_status(msg, ACCENT2)
        if self.console:
            self.console.write_ok(msg)

    def _do_run_step(self):
        self._core.run_step()
        self._refresh_registers()
        msg = "RUN STEP  ·  un ciclo fetch-decode-execute completado"
        self._set_status(msg, ACCENT5)
        if self.console:
            regs = self._core.processor.get_registers()
            self.console.write_info(msg)
            self.console.write_hex("PC", regs.get("pc", 0), bits=64)
            self.console.write_hex("IR", regs.get("ir", 0), bits=64)

    # ─────────────────────────────────────────────────────────────────────
    #  RAM EDITOR (ventana independiente)
    # ─────────────────────────────────────────────────────────────────────
    def _open_ram_editor(self):
        if hasattr(self, "_ram_win") and self._ram_win and \
                self._ram_win.winfo_exists():
            self._ram_win.lift()
            self._ram_win.focus_force()
            return

        base = os.path.dirname(os.path.abspath(__file__))
        editor_path = None
        for candidate in [
            os.path.join(base, "memoria", "cacao_ram_editor.py"),
            os.path.join(base, "cacao_ram_editor.py"),
        ]:
            if os.path.exists(candidate):
                editor_path = candidate
                break

        if editor_path is None:
            msg = "No se encontro cacao_ram_editor.py"
            messagebox.showinfo("RAM Editor",
                f"{msg}\nRuta esperada: src/memoria/cacao_ram_editor.py")
            if self.console:
                self.console.write_warn(msg)
            return

        import importlib.util
        spec = importlib.util.spec_from_file_location("cacao_ram_editor",
                                                       editor_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        EditorClass = mod.CacaoRAMEditor

        parent_self = self

        class RAMEditorWindow(tk.Toplevel):
            def __init__(self):
                super().__init__(parent_self)
                self.title("CACAO_Core-64  ·  Editor de RAM")
                self.geometry("1260x820")
                self.minsize(1100, 700)
                self.configure(bg=mod.BG_DARK)
                self.loader_mod = loader_txt
                self.resizable(True, True)
                self._zoom_manager = None
                self.loaded_file_path = None
                self.addr_var      = tk.StringVar(self, value="00001000")
                self.data_mode     = tk.StringVar(self, value="hex")
                self.read_addr_var = tk.StringVar(self, value="00001000")
                self.read_len_var  = tk.StringVar(self, value="64")
                self.hex_base_var  = tk.StringVar(self, value="00001000")
                self.hex_rows_var  = tk.StringVar(self, value="16")
                self._palette_name = "current"
                import types
                for name in dir(EditorClass):
                    if name.startswith("__"):
                        continue
                    val = getattr(EditorClass, name)
                    if callable(val) and isinstance(val, types.FunctionType):
                        setattr(self, name, types.MethodType(val, self))
                self._build_ui()
                self._refresh_hex_view(0x00001000, 16)

        win = RAMEditorWindow()
        self._ram_win = win
        msg = "RAM Editor abierto en proceso compartido — cambios inmediatos."
        self._set_status(msg, mod.ACCENT)
        if self.console:
            self.console.write_ok(msg)
    
    def _set_status(self, msg, color=ACCENT):
        self._status_var.set(f"  {msg}")
        self._status_lbl.config(fg=color)

    def _toggle_settings_popup(self):
        self._zoom_manager.toggle_settings_popup()

    def _apply_palette(self, palette_name):
        self._palette_name = palette_name
        apply_palette_namespace(globals(), palette_name)
        apply_palette_namespace(styles_cacao_module.__dict__, palette_name)
        apply_palette_namespace(styles_console_module.__dict__, palette_name)
        apply_palette_namespace(compiler_gui_module.__dict__, palette_name)
        apply_palette_namespace(cacao_console_module.__dict__, palette_name)
        recolor_widget_tree(self, palette_name)
        if self._zoom_manager is not None:
            self._zoom_manager.apply_zoom("both")
    
    def _open_compiler(self):
        compiler = CompilerGui(self)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = CacaoCoreGUI()
    app.mainloop()
