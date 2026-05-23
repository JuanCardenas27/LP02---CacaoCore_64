import os
import time
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import gui.styles_cacao as styles_cacao_module
import gui.styles_spl as styles_spl_module
from gui.styles_spl import *
from gui.theme_manager import apply_palette_namespace, recolor_widget_tree
from gui.zoom_manager import ZoomManager
from assembler import ASM, ASMLexicError, ASMParseError
from compiler import compiler
from enlazador_cargador.linker import Linker, LinkerError
from preprocesador import Preprocesador, PreprocesadorError


class CompilerGui:
    def __init__(self, master):
        self.window = tk.Toplevel(master, bg=BG_DARK)
        self.window.title("Language Processing")

        width  = int(self.window.winfo_screenwidth()  * 0.98)
        height = int(self.window.winfo_screenheight() * 0.9)
        self.window.geometry(f"{width}x{height}+0+0")
        self.window.resizable(False, False)
        self.window.lift()

        self.index           = 0
        self.compiler_step   = 0
        self._carry_compiler = ""   # texto que viaja de pre-processor → compiler
        self._carry_loader   = ""   # texto que viaja de assembler     → link&load
        self._zoom_manager   = None
        self._palette_name    = "current"
        self._pc_source_path = None
        self._core = getattr(master, "_core", None)
        self.fs = self._core.fs if self._core else None

        # Incializa estilos 
        setup_styles()

        self._create_body()
        self._setup_header()
        self._setup_body()
        self._set_menu()
        self._pre_compiler()
        self._init_zoom_controls()

    # ══════════════════════════════════════════════════════════════════════
    # ESTRUCTURA BASE
    # ══════════════════════════════════════════════════════════════════════

    def _create_body(self):
        self.window.grid_rowconfigure(0, weight=0)
        self.window.grid_rowconfigure(1, weight=0)
        self.window.grid_rowconfigure(2, weight=0)
        self.window.grid_rowconfigure(3, weight=10)
        self.window.grid_columnconfigure(0, weight=1)

        self.header = tk.Frame(self.window, bg=BG_MID,
                               highlightbackground=BORDER, highlightthickness=2)
        self.header.grid(row=2, column=0, sticky="nsew")

        self.body = tk.Frame(self.window, bg=BG_MID,
                             highlightbackground=BORDER, highlightthickness=2)
        self.body.grid(row=3, column=0, sticky="nsew")

        self._build_logo()

    def _build_logo(self):
        hdr = tk.Frame(self.window, bg=BG_DARK, pady=10)
        hdr.grid(row=0, column=0, padx=18, sticky="nsew")

        canvas = tk.Canvas(hdr, width=40, height=40, bg=BG_DARK, highlightthickness=0)
        canvas.pack(side="left", padx=(0, 10))
        for r in range(5):
            for c in range(5):
                if (r + c) % 2 == 0:
                    canvas.create_rectangle(c*8, r*8, c*8+7, r*8+7, fill=ACCENT, outline="")

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
            text="   LANGUAGE PROCESSOR SYSTEM",
            font=("Courier New", 14),
            fg=ACCENT2,
            bg=BG_DARK,
        )
        self._hdr_subtitle.pack(side="left")

        tk.Frame(hdr, bg=BG_DARK).pack(side="left", fill="x", expand=True)

        self._settings_btn = tk.Button(
            hdr,
            text="⚙️ Configurar",
            bg=BG_MID,
            fg=ACCENT4,
            activebackground=ACCENT4,
            activeforeground=BG_DARK,
            relief="flat",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._toggle_settings_popup,
        )
        self._settings_btn.pack(side="left", padx=(20, 20))

        self._hdr_info = tk.Label(
            hdr,
            text="64-bit  ·  Von Neumann  ·  1 MB RAM",
            font=FM_SM,
            fg=TEXT_DIM,
            bg=BG_DARK,
        )
        self._hdr_info.pack(side="left")

        tk.Frame(self.window, bg=ACCENT, height=2).grid(row=1, column=0, sticky="ew")

    def _setup_header(self):
        self.header.grid_rowconfigure(0, weight=1)
        self.header.grid_columnconfigure(0, weight=1)

        panel = tk.Frame(self.header, bg=BG_PANEL,
                         highlightbackground=BORDER, highlightthickness=2)
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        for col in range(4):
            panel.grid_columnconfigure(col, weight=1, uniform="spl_phase")

        phases = ["Pre-Processor", "Compiler", "Assembler", "Loader / Linker"]
        colors = [ACCENT, ACCENT2, ACCENT3, ACCENT4]
        cmds   = [self._pre_compiler, self._compiler, self._assembler, self._link_load]

        self._phase_btns = []
        for i, (text, color, cmd) in enumerate(zip(phases, colors, cmds)):
            btn = tk.Button(panel, text=text, bg=color, fg=BG_DARK,
                            font=FM_BTN_CMP, activebackground=TEXT_MAIN,
                            activeforeground="black", bd=0,
                            padx=25, pady=15, cursor="hand2",
                            command=lambda c=cmd, idx=i: self._switch_phase(c, idx))
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self._phase_btns.append(btn)

    def _switch_phase(self, cmd, idx):
        """Botones del header: navegan sin carry (acceso directo)."""
        self.index = idx
        self._set_menu()
        cmd()

    def _setup_body(self):
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=3, uniform="spl_body")
        self.body.grid_columnconfigure(1, weight=1, uniform="spl_body", minsize=280)

        self.content = tk.Frame(self.body, bg=BG_PANEL)
        self.content.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.menu = tk.Frame(self.body, bg=BG_PANEL)
        self.menu.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    def _set_menu(self):
        for w in self.menu.winfo_children():
            w.destroy()

        self.menu.grid_rowconfigure(0, weight=1)
        self.menu.grid_rowconfigure(1, weight=1)
        self.menu.grid_columnconfigure(0, weight=1)

        phase_names = ["Pre-Processor", "Compiler", "Assembler", "Loader / Linker"]
        colors      = [ACCENT, ACCENT2, ACCENT3, ACCENT4]

        tk.Label(self.menu,
                 text=f"Current phase:\n{phase_names[self.index]}",
                 bg=colors[self.index], fg=BG_DARK,
                 font=FM_LG, justify="center"
                 ).grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        tk.Button(self.menu, text="Continue ▶",
                  bg=ACCENT, fg=BG_DARK, font=FM_BTN_1,
                  bd=0, padx=20, pady=15, cursor="hand2",
                  command=self._next_phase
                  ).grid(row=1, column=0, pady=10)

        self._refresh_zoom_dynamic()

    def _init_zoom_controls(self):
        if self._zoom_manager is not None:
            return

        self._zoom_manager = ZoomManager(
            self.window,
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
            scale_widget_size=False,
            on_palette_change=self._apply_palette,
            initial_palette=self._palette_name,
        )
        self._zoom_manager.attach_widgets(
            header_title=self._hdr_title,
            header_subtitle=self._hdr_subtitle,
            header_info=self._hdr_info,
            settings_button=self._settings_btn,
            status_label=None,
            reg_labels={},
            flag_widgets_alu={},
            flag_widgets_fau={},
            format_rbs=[],
        )
        self._zoom_manager.initialize()

    def _toggle_settings_popup(self):
        if self._zoom_manager is not None:
            self._zoom_manager.toggle_settings_popup()

    def _apply_palette(self, palette_name):
        self._palette_name = palette_name
        apply_palette_namespace(globals(), palette_name)
        apply_palette_namespace(styles_cacao_module.__dict__, palette_name)
        apply_palette_namespace(styles_spl_module.__dict__, palette_name)
        setup_styles()
        recolor_widget_tree(self.window, palette_name)
        if self._zoom_manager is not None:
            self._zoom_manager.apply_zoom("both")

    def _refresh_zoom_dynamic(self):
        """Reaplica zoom actual sobre widgets recreados en cambios de fase/paso."""
        if self._zoom_manager is None:
            return
        self.window.update_idletasks()
        self._zoom_manager.capture_original_values()
        self._zoom_manager.apply_zoom("both")

    # ══════════════════════════════════════════════════════════════════════
    # UTILIDADES INTERNAS
    # ══════════════════════════════════════════════════════════════════════

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()
        for r in range(10):
            self.content.grid_rowconfigure(r, weight=0)
        for c in range(10):
            self.content.grid_columnconfigure(c, weight=0)

    def _scrollable_text(self, parent, fg=TEXT_MAIN, state="normal", font=None):
        if font is None:
            font = FM
        frame = tk.Frame(parent, bg=BG_INPUT,
                         highlightbackground=BORDER, highlightthickness=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        sb = tk.Scrollbar(frame, orient="vertical", bg=BG_MID,
                          troughcolor=BG_DARK, activebackground=ACCENT2)
        sb.grid(row=0, column=1, sticky="ns")

        txt = tk.Text(frame, bg=BG_INPUT, fg=fg,
                      insertbackground=ACCENT2, font=font,
                      wrap="word", padx=8, pady=8, bd=0,
                      yscrollcommand=sb.set, state=state)
        txt.grid(row=0, column=0, sticky="nsew")
        sb.config(command=txt.yview)

        return frame, txt

    def _section_label(self, parent, text, fg):
        return tk.Label(parent, text=text, bg=BG_PANEL,
                        fg=fg, font=FM_BTN, anchor="w")

    def _action_btn(self, parent, text, color, cmd):
        return tk.Button(parent, text=text, bg=color, fg=BG_DARK,
                         font=FM_BTN_1, bd=0, padx=18, pady=10,
                         cursor="hand2", command=cmd)
    
    def _scrollable_table(self, parent, columns):
        frame = tk.Frame(parent, bg=BG_INPUT,
                        highlightbackground=BORDER, highlightthickness=1)

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        table = ttk.Treeview(frame, columns=columns, show="headings", style="SymbolTable.Treeview")
        for col in columns:
            table.heading(col, text=col)
            table.column(col, anchor="center", width=100, stretch=True)

        table.grid(row=0, column=0, sticky="nsew")

        # Scroll vertical
        vsb = tk.Scrollbar(frame, orient="vertical", command=table.yview)
        vsb.grid(row=0, column=1, sticky="ns")

        # Scroll horizontal
        hsb = tk.Scrollbar(frame, orient="horizontal", command=table.xview)
        hsb.grid(row=1, column=0, sticky="ew")

        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        return frame, table

    # ══════════════════════════════════════════════════════════════════════
    # FASE 0 – PRE-PROCESSOR
    # ══════════════════════════════════════════════════════════════════════

    def _pre_compiler(self, carry=""):
        self._clear_content()

        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=0)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=1)

        # ── Columna izquierda ────────────────────────────────────────────
        left = tk.Frame(self.content, bg=BG_PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._section_label(left, "◈  HIGH-LEVEL SOURCE", ACCENT2
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))

        tf_l, self.pc_hl = self._scrollable_text(left, fg=TEXT_MAIN)
        tf_l.grid(row=1, column=0, sticky="nsew")

        # ── Columna derecha ──────────────────────────────────────────────
        right = tk.Frame(self.content, bg=BG_PANEL)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._section_label(right, "◈  PRE-PROCESSED OUTPUT", ACCENT
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))

        tf_r, self.pc_out = self._scrollable_text(right, fg=ACCENT, state="disabled")
        tf_r.grid(row=1, column=0, sticky="nsew")

        # ── Barra de botones ─────────────────────────────────────────────
        btn_bar = tk.Frame(self.content, bg=BG_PANEL)
        btn_bar.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        self._action_btn(btn_bar, "⚙  Pre-process", ACCENT,
                         self._do_precompile).pack(side="left", padx=10)
        self._action_btn(btn_bar, "⬆  Load file", ACCENT2,
                         self._pc_load_file).pack(side="left", padx=10)
        self._action_btn(btn_bar, "✕  Erase", ACCENT3,
                         self._pc_erase).pack(side="left", padx=10)

        self._refresh_zoom_dynamic()

    def _pc_load_file(self):
        def apply_load(name: str, data: str) -> None:
            self.pc_hl.delete("1.0", tk.END)
            self.pc_hl.insert("1.0", data)
            self._pc_source_path = f"<disk:{name}>"

        self._load_file_with_preview(
            [".choco", ".chocolate", ".txt"],
            "Previsualizar archivo",
            apply_load,
        )

    def _pc_erase(self):
        self.pc_hl.delete("1.0", tk.END)
        self.pc_out.configure(state="normal")
        self.pc_out.delete("1.0", tk.END)
        self.pc_out.configure(state="disabled")
        self._pc_source_path = None

    # ══════════════════════════════════════════════════════════════════════
    # FASE 1 – COMPILER  (léxico / sintáctico / semántico)
    # ══════════════════════════════════════════════════════════════════════

    def _compiler(self, carry=""):
        self._carry_compiler = carry   # guardar para inyectar en lex_input
        self.compiler_step   = 0
        self._build_compiler_step()

    def _build_compiler_step(self):
        self._clear_content()

        self.content.grid_rowconfigure(0, weight=0)
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_rowconfigure(2, weight=0)
        self.content.grid_columnconfigure(0, weight=1)

        steps      = ["Lexical Analysis", "Syntactic Analysis", "Semantic Analysis"]
        step_color = [ACCENT2, ACCENT3, ACCENT5]

        # ── Barra de navegación ──────────────────────────────────────────
        nav = tk.Frame(self.content, bg=BG_PANEL)
        nav.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        nav.grid_columnconfigure(1, weight=1)

        self.btn_prev = tk.Button(nav, text="◀  Prev",
                                  bg=TEXT_DIM, fg=BG_DARK,
                                  font=FM_BTN, bd=0, padx=14, pady=8,
                                  cursor="hand2", command=self._compiler_prev)
        self.btn_prev.grid(row=0, column=0, padx=(0, 10))

        tk.Label(nav, text=steps[self.compiler_step],
                 bg=step_color[self.compiler_step], fg=BG_DARK,
                 font=FM_LG, padx=20, pady=8
                 ).grid(row=0, column=1)

        self.btn_next = tk.Button(nav, text="Next  ▶",
                                  bg=TEXT_DIM, fg=BG_DARK,
                                  font=FM_BTN, bd=0, padx=14, pady=8,
                                  cursor="hand2", command=self._compiler_next)
        self.btn_next.grid(row=0, column=2, padx=(10, 0))

        if self.compiler_step == 0:
            self.btn_prev.configure(state="disabled", bg=BG_MID)
        if self.compiler_step == 2:
            self.btn_next.configure(state="disabled", bg=BG_MID)

        # ── Área de contenido ────────────────────────────────────────────
        area = tk.Frame(self.content, bg=BG_PANEL)
        area.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        area.grid_rowconfigure(0, weight=1)
        area.grid_columnconfigure(0, weight=1)
        area.grid_columnconfigure(1, weight=1)
        area.grid_columnconfigure(2, weight=1)

        if self.compiler_step == 0:
            self._build_lexical(area)
        elif self.compiler_step == 1:
            self._build_syntactic(area)
        else:
            self._build_semantic(area)

        self._refresh_zoom_dynamic()

    # ── Paso 0: Léxico ────────────────────────────────────────────────────

    def _build_lexical(self, area):
        # Izquierda: código pre-procesado
        left = tk.Frame(area, bg=BG_PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._section_label(left, "◈  PRE-PROCESSED INPUT", ACCENT2
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))
        tf_l, self.lex_input = self._scrollable_text(left)
        tf_l.grid(row=1, column=0, sticky="nsew")

        # Inyectar carry proveniente del pre-processor
        if self._carry_compiler.strip():
            self.lex_input.insert("1.0", self._carry_compiler.strip())

        # Centro: tokens
        center = tk.Frame(area, bg=BG_PANEL)
        center.grid(row=0, column=1, sticky="nsew", padx=(0, 5))
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)

        self._section_label(center, "◈  Tokens identified", ACCENT3
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))
        tf_c, self.lex_tokens = self._scrollable_text(center)
        tf_c.grid(row=1, column=0, sticky="nsew")

        # Derecha: tabla de símbolos + errores
        right = tk.Frame(area, bg=BG_PANEL)
        right.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_rowconfigure(3, weight=1)
        right.grid_rowconfigure(5, weight=2)
        right.grid_columnconfigure(0, weight=1)

        self._section_label(right, "◈  Symbol Table", ACCENT4
                            ).grid(row=0, column=0, sticky="ew", pady=(3, 1))
        columns = ['Lexeme', 'Length', 'Lines', 'Kind', 'Type', 'Value', 'Scope']
        tf_r, self.lex_symbol = self._scrollable_table(right, columns)
        tf_r.grid(row=1, column=0, sticky="nsew")

        self._section_label(right, "◈  Numeric Symbol Table", ACCENT3
                            ).grid(row=2, column=0, sticky="ew", pady=(3, 1))
        columns = ['Lexeme', 'Type', 'Value', 'Line']
        tf_n, self.num_symbol = self._scrollable_table(right, columns)
        tf_n.grid(row=3, column=0, sticky="nsew")

        self._section_label(right, "◈  Errores", ACCENT5
                            ).grid(row=4, column=0, sticky="ew", pady=(3, 1))
        tf_e, self.lex_error = self._scrollable_text(right, fg=ACCENT5, state="disabled", font=FM_SM)
        tf_e.grid(row=5, column=0, sticky="nsew")

        # Botón
        btn_bar = tk.Frame(self.content, bg=BG_PANEL)
        btn_bar.grid(row=2, column=0, pady=(0, 10))
        self._action_btn(btn_bar, "⚙  Start Lexical Analysis", ACCENT2,
                         self._do_lexical).pack()

    # ── Paso 1: Sintáctico ────────────────────────────────────────────────

    def _build_syntactic(self, area):
        tk.Label(area, text="[ Syntactic Analysis — coming soon ]",
                 bg=BG_PANEL, fg=TEXT_DIM, font=FM_LG
                 ).grid(row=0, column=0, columnspan=3, pady=40)

    # ── Paso 2: Semántico ─────────────────────────────────────────────────

    def _build_semantic(self, area):
        tk.Label(area, text="[ Semantic Analysis — coming soon ]",
                 bg=BG_PANEL, fg=TEXT_DIM, font=FM_LG
                 ).grid(row=0, column=0, columnspan=3, pady=40)

    def _compiler_prev(self):
        if self.compiler_step > 0:
            self.compiler_step -= 1
            self._build_compiler_step()

    def _compiler_next(self):
        if self.compiler_step < 2:
            self.compiler_step += 1
            self._build_compiler_step()

    # ══════════════════════════════════════════════════════════════════════
    # FASE 2 – ASSEMBLER
    # ══════════════════════════════════════════════════════════════════════

    def _assembler(self, carry=""):
        self._clear_content()

        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=0)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=0)
        self.content.grid_columnconfigure(2, weight=1)

        # ── Izquierda: fuente ASM ────────────────────────────────────────
        left = tk.Frame(self.content, bg=BG_PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 4), pady=10)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._section_label(left, "◈  ASSEMBLY SOURCE", ACCENT2
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))
        tf_l, self.asm_src = self._scrollable_text(left)
        tf_l.grid(row=1, column=0, sticky="nsew")

        # ── Centro (separador visual) ────────────────────────────────────
        mid = tk.Frame(self.content, bg=BG_PANEL)
        mid.grid(row=0, column=1, sticky="nsew", pady=10)
        mid.grid_rowconfigure(0, weight=1)
        mid.grid_columnconfigure(0, weight=1)

        # ── Derecha: código relocalizable ───────────────────────────────
        right = tk.Frame(self.content, bg=BG_PANEL)
        right.grid(row=0, column=2, sticky="nsew", padx=(4, 10), pady=10)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._section_label(right, "◈  RELOCATABLE OUTPUT", ACCENT5
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))
        tf_r, self.asm_out = self._scrollable_text(right, fg=ACCENT5, state="disabled")
        tf_r.grid(row=1, column=0, sticky="nsew")

        # ── Botones inferiores ───────────────────────────────────────────
        btn_bar = tk.Frame(self.content, bg=BG_PANEL)
        btn_bar.grid(row=1, column=0, columnspan=3, pady=(0, 10))

        self._action_btn(btn_bar, "⬆  Load ASM file", ACCENT2,
                         self._asm_load).pack(side="left", padx=10)
        self._action_btn(btn_bar, "▶  TRANSLATE", ACCENT,
                         self._translate_asm).pack(side="left", padx=10)
        self._action_btn(btn_bar, "✕  Erase", ACCENT3,
                         self._asm_erase).pack(side="left", padx=10)

        self._refresh_zoom_dynamic()

    def _asm_load(self):
        def apply_load(_name: str, data: str) -> None:
            self.asm_src.delete("1.0", tk.END)
            self.asm_src.insert("1.0", data)

        self._load_file_with_preview(
            [".cacao", ".asm"],
            "Previsualizar ASM",
            apply_load,
        )

    def _asm_erase(self):
        self.asm_src.delete("1.0", tk.END)
        self.asm_out.configure(state="normal")
        self.asm_out.delete("1.0", tk.END)
        self.asm_out.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════════
    # FASE 3 – LOADER / LINKER
    # ══════════════════════════════════════════════════════════════════════

    def _link_load(self, carry=""):
        self._carry_loader = carry     # guardar para inyectar en ll_reloc
        self._clear_content()

        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=0)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=1)

        # ── Izquierda: código relocalizable ─────────────────────────────
        left = tk.Frame(self.content, bg=BG_PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._section_label(left, "◈  RELOCATABLE CODE", ACCENT5
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))
        tf_l, self.ll_reloc = self._scrollable_text(left, fg=ACCENT5)
        tf_l.grid(row=1, column=0, sticky="nsew")

        # Inyectar carry proveniente del assembler
        if self._carry_loader.strip():
            self.ll_reloc.insert("1.0", self._carry_loader.strip())

        # ── Derecha: código cargado en memoria ───────────────────────────
        right = tk.Frame(self.content, bg=BG_PANEL)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._section_label(right, "◈  MEMORY-LOADED CODE", ACCENT
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))

        addr_row = tk.Frame(right, bg=BG_PANEL)
        addr_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        addr_row.grid_columnconfigure(1, weight=1)

        tk.Label(addr_row, text="BASE ADDR (hex)  0x",
                 bg=BG_PANEL, fg=ACCENT4, font=FM_BTN
                 ).grid(row=0, column=0, sticky="w")

        self.ll_base_addr = tk.Entry(
            addr_row, bg=BG_INPUT, fg=ACCENT4,
            insertbackground=ACCENT4, font=FM_LG,
            bd=0, highlightbackground=BORDER,
            highlightthickness=1, justify="center", width=12
        )
        self.ll_base_addr.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.ll_base_addr.insert(0, "00001000")

        tf_r, self.ll_loaded = self._scrollable_text(right, fg=ACCENT, state="disabled")
        tf_r.grid(row=2, column=0, sticky="nsew")

        # ── Botones inferiores ───────────────────────────────────────────
        btn_bar = tk.Frame(self.content, bg=BG_PANEL)
        btn_bar.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        self._action_btn(btn_bar, "⬆  Load reloc file", ACCENT5,
                         self._ll_load).pack(side="left", padx=10)
        self._action_btn(btn_bar, "⚙  Link & Load", ACCENT,
                         self._do_link_load).pack(side="left", padx=10)
        self._action_btn(btn_bar, "✕  Erase", ACCENT3,
                         self._ll_erase).pack(side="left", padx=10)

        self._refresh_zoom_dynamic()

    def _do_link_load(self):
            """
            Lee el código relocalizable de self.ll_reloc, toma la dirección base
            de self.ll_base_addr, invoca el Linker y muestra el resultado en
            self.ll_loaded.  También escribe los bytes directamente en la RAM global.
            """
            # ── Leer entradas ────────────────────────────────────────────────
            reloc_text = self.ll_reloc.get("1.0", tk.END).strip()
            if not reloc_text:
                self._ll_show_error("No hay código relocalizable para procesar.")
                return

            raw_addr = self.ll_base_addr.get().strip().lstrip("0x").lstrip("0X")
            if not raw_addr:
                raw_addr = "0"
            try:
                base_address = int(raw_addr, 16)
            except ValueError:
                self._ll_show_error(
                    f"Dirección base inválida: '0x{raw_addr}'\n"
                    "Ingrese un valor hexadecimal válido (ej. 00001000)."
                )
                return

            # ── Ejecutar el enlazador/cargador ───────────────────────────────
            linker = Linker()
            try:
                output_text = linker.link_and_load(reloc_text, base_address)
            except LinkerError as exc:
                self._ll_show_error(f"Error de enlazado:\n{exc}")
                return
            except Exception as exc:
                self._ll_show_error(f"Error inesperado:\n{exc}")
                return

            # ── Mostrar resultado en ll_loaded ───────────────────────────────
            self.ll_loaded.configure(state="normal")
            self.ll_loaded.delete("1.0", tk.END)
            self.ll_loaded.insert("1.0", output_text)
            self.ll_loaded.configure(state="disabled")

    def _ll_show_error(self, message: str) -> None:
        """Muestra un mensaje de error en el panel de salida ll_loaded."""
        self.ll_loaded.configure(state="normal")
        self.ll_loaded.delete("1.0", tk.END)
        self.ll_loaded.insert("1.0", f"[ERROR]\n{message}")
        self.ll_loaded.configure(state="disabled")

    def _ll_load(self):
        def apply_load(_name: str, data: str) -> None:
            self.ll_reloc.delete("1.0", tk.END)
            self.ll_reloc.insert("1.0", data)

        self._load_file_with_preview(
            [".reloc", ".txt"],
            "Previsualizar reloc",
            apply_load,
        )

    def _load_file_with_preview(self, allowed_exts, title, on_accept) -> None:
        if not self.fs:
            messagebox.showerror(
                "Disco",
                "No hay sistema de archivos disponible.",
            )
            return
        self._show_disk_picker(title, allowed_exts, on_accept)

    def _show_disk_picker(self, title, allowed_exts, on_accept) -> None:
        dialog = tk.Toplevel(self.window)
        dialog.title(title)
        dialog.configure(bg=BG_DARK)
        dialog.geometry("1200x720")
        dialog.minsize(1000, 600)
        dialog.transient(self.window)

        hdr = tk.Frame(dialog, bg=BG_DARK, pady=8)
        hdr.pack(fill="x", padx=16)

        tk.Label(hdr, text="Disco local", font=FM_LG, fg=ACCENT2, bg=BG_DARK).pack(side="left")

        def apply_tree_style():
            style = ttk.Style(dialog)
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass
            style.configure(
                "Disk.Treeview",
                background=BG_MID,
                fieldbackground=BG_MID,
                foreground=TEXT_MAIN,
                rowheight=24,
                bordercolor=BORDER,
                relief="flat",
            )
            style.configure(
                "Disk.Treeview.Heading",
                background=BG_PANEL,
                foreground=ACCENT,
                relief="flat",
                font=FM_BTN,
            )
            style.map(
                "Disk.Treeview",
                background=[("selected", ACCENT2)],
                foreground=[("selected", BG_DARK)],
            )

        body = tk.Frame(dialog, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=8)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1, uniform="disk_cols")
        body.grid_columnconfigure(1, weight=2, uniform="disk_cols")

        left = tk.Frame(body, bg=BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right = tk.Frame(body, bg=BG_DARK)
        right.grid(row=0, column=1, sticky="nsew")

        list_outer = tk.Frame(left, bg=BORDER, pady=1)
        list_outer.pack(fill="both", expand=True)
        list_inner = tk.Frame(list_outer, bg=BG_PANEL, padx=10, pady=8)
        list_inner.pack(fill="both", expand=True)

        tk.Label(
            list_inner,
            text="◈  ARCHIVOS EN DISCO",
            font=FM_BTN,
            fg=ACCENT2,
            bg=BG_PANEL,
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        search_row = tk.Frame(list_inner, bg=BG_PANEL)
        search_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            search_row,
            text="Buscar:",
            font=FM_SM,
            fg=TEXT_DIM,
            bg=BG_PANEL,
        ).pack(side="left")
        search_var = tk.StringVar(value="")
        search_entry = tk.Entry(
            search_row,
            textvariable=search_var,
            font=FM,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT,
            relief="flat",
            bd=4,
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=6)

        apply_tree_style()

        columns = ("name", "size", "mtime")
        files_list = ttk.Treeview(
            list_inner,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=16,
            style="Disk.Treeview",
        )
        files_list.heading("name", text="Archivo")
        files_list.heading("size", text="Tam")
        files_list.heading("mtime", text="Modificado")
        files_list.column("name", width=220, anchor="w")
        files_list.column("size", width=80, anchor="e")
        files_list.column("mtime", width=140, anchor="center")
        files_list.pack(fill="both", expand=True)

        btn_row = tk.Frame(list_inner, bg=BG_PANEL)
        btn_row.pack(fill="x", pady=(8, 0))
        tk.Button(
            btn_row,
            text="⟳  REFRESCAR",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT,
            relief="flat",
            cursor="hand2",
            command=lambda: refresh_list(clear_selection=True),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(
            search_row,
            text="✕",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT4,
            relief="flat",
            cursor="hand2",
            command=lambda: clear_search(),
        ).pack(side="left")

        preview_outer = tk.Frame(right, bg=BORDER, pady=1)
        preview_outer.pack(fill="both", expand=True)
        preview_inner = tk.Frame(preview_outer, bg=BG_PANEL, padx=10, pady=8)
        preview_inner.pack(fill="both", expand=True)

        tk.Label(
            preview_inner,
            text="◈  PREVISUALIZAR",
            font=FM_BTN,
            fg=ACCENT,
            bg=BG_PANEL,
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        name_row = tk.Frame(preview_inner, bg=BG_PANEL)
        name_row.pack(fill="x", pady=(0, 6))
        tk.Label(
            name_row,
            text="Nombre:",
            font=FM_SM,
            fg=TEXT_DIM,
            bg=BG_PANEL,
        ).pack(side="left")
        name_var = tk.StringVar(value="")
        name_entry = tk.Entry(
            name_row,
            textvariable=name_var,
            font=FM,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT,
            relief="flat",
            bd=4,
            state="readonly",
        )
        name_entry.pack(side="left", fill="x", expand=True, padx=6)

        action_row = tk.Frame(preview_inner, bg=BG_PANEL)
        action_row.pack(fill="x", pady=(0, 6))

        preview = tk.Text(
            preview_inner,
            font=FM,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT,
            relief="flat",
            wrap="none",
            bd=8,
        )
        preview.configure(state="disabled")
        sb = ttk.Scrollbar(preview_inner, orient="vertical", command=preview.yview)
        preview.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        preview.pack(fill="both", expand=True)

        selection = {"name": None, "data": None}
        load_visible = {"shown": False}

        def fmt_size(size_bytes: int) -> str:
            if size_bytes < 1024:
                return f"{size_bytes} B"
            size_kb = size_bytes / 1024.0
            if size_kb < 1024:
                return f"{size_kb:.1f} KB"
            size_mb = size_kb / 1024.0
            if size_mb < 1024:
                return f"{size_mb:.1f} MB"
            size_gb = size_mb / 1024.0
            return f"{size_gb:.2f} GB"

        def set_load_visible(visible: bool) -> None:
            if visible and not load_visible["shown"]:
                load_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
                load_visible["shown"] = True
            elif not visible and load_visible["shown"]:
                load_btn.pack_forget()
                load_visible["shown"] = False

        def clear_preview():
            selection["name"] = None
            selection["data"] = None
            name_var.set("")
            preview.configure(state="normal")
            preview.delete("1.0", "end")
            preview.configure(state="disabled")
            set_load_visible(False)

        def refresh_list(clear_selection: bool = False) -> None:
            files_list.delete(*files_list.get_children())
            query = search_var.get().strip().lower()
            entries = self.fs.list_files()
            if allowed_exts:
                allowed = set(ext.lower() for ext in allowed_exts)
                entries = [
                    entry
                    for entry in entries
                    if os.path.splitext(entry.get("name", ""))[1].lower() in allowed
                ]
            entries.sort(key=lambda e: e.get("name", ""))
            for entry in entries:
                name = entry.get("name", "")
                if query and query not in name.lower():
                    continue
                size_txt = fmt_size(entry.get("size", 0))
                mtime = entry.get("mtime", 0)
                mtime_txt = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime)) if mtime else "-"
                files_list.insert("", "end", values=(name, size_txt, mtime_txt))
            if clear_selection:
                clear_preview()

        def clear_search() -> None:
            search_var.set("")
            refresh_list(clear_selection=True)

        def load_preview(_evt=None) -> None:
            clear_preview()
            if not files_list.selection():
                return
            name = files_list.item(files_list.selection()[0], "values")[0]
            try:
                data = self.fs.read_file(name)
            except Exception as exc:
                messagebox.showerror("Disco", f"No se pudo leer '{name}':\n{exc}")
                return
            text = data.decode("utf-8", errors="replace")
            preview.configure(state="normal")
            preview.insert("1.0", text)
            preview.configure(state="disabled")
            selection["name"] = name
            selection["data"] = text
            name_var.set(name)
            set_load_visible(True)

        def accept() -> None:
            if not selection["name"]:
                messagebox.showinfo("Disco", "Selecciona un archivo")
                return
            on_accept(selection["name"], selection["data"] or "")
            dialog.destroy()

        load_btn = tk.Button(
            action_row,
            text="📂  CARGAR",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT2,
            relief="flat",
            cursor="hand2",
            command=accept,
        )
        set_load_visible(False)

        tk.Button(
            action_row,
            text="✕  CANCELAR",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT4,
            relief="flat",
            cursor="hand2",
            command=dialog.destroy,
        ).pack(side="right", fill="x", expand=True)

        refresh_list(clear_selection=True)
        files_list.bind("<<TreeviewSelect>>", load_preview)
        files_list.bind("<Double-1>", lambda _e: (load_preview(), accept()))
        search_entry.bind("<KeyRelease>", lambda _e: refresh_list(clear_selection=True))

    def _ll_erase(self):
        self.ll_reloc.delete("1.0", tk.END)
        self.ll_loaded.configure(state="normal")
        self.ll_loaded.delete("1.0", tk.END)
        self.ll_loaded.configure(state="disabled")
        self.ll_base_addr.delete(0, tk.END)
        self.ll_base_addr.insert(0, "0000")

    # ══════════════════════════════════════════════════════════════════════
    # NAVEGACIÓN
    # ══════════════════════════════════════════════════════════════════════

    def _next_phase(self):
        cmds = [self._pre_compiler, self._compiler, self._assembler, self._link_load]
        if self.index >= len(cmds) - 1:
            return

        carry = ""
        if self.index == 0:        # pre-processor → compiler: llevar pc_out
            try:
                carry = self.pc_out.get("1.0", tk.END)
            except Exception:
                carry = ""
        elif self.index == 2:      # assembler → link&load: llevar asm_out
            try:
                carry = self.asm_out.get("1.0", tk.END)
            except Exception:
                carry = ""

        self.index += 1
        self._set_menu()
        cmds[self.index](carry=carry)

    # ══════════════════════════════════════════════════════════════════════
    # LÓGICA DE PROCESAMIENTO
    # ══════════════════════════════════════════════════════════════════════

    def _do_precompile(self):
        codigo = self.pc_hl.get("1.0", tk.END)
        pre = Preprocesador()

        try:
            nombre_fuente = self._pc_source_path or "<gui>"
            resultado = pre.preprocess(codigo, nombre_fuente=nombre_fuente)
            salida = resultado.text
        except PreprocesadorError as exc:
            salida = str(exc)

        self.pc_out.configure(state="normal")
        self.pc_out.delete("1.0", tk.END)
        self.pc_out.insert("1.0", salida)
        self.pc_out.configure(state="disabled")

    def _do_lexical(self):
        resultado    = compiler.compile(self.lex_input.get("1.0", "end"))
        lex_errors = resultado[0]
        symbol_table = resultado[1]
        tokens = resultado[2]
        number_table = resultado[3]

        self.lex_tokens.config(state="normal")
        self.lex_tokens.delete("1.0", tk.END)
        for tkn in tokens:
            self.lex_tokens.insert(tk.END, f"{tkn.type}: {tkn.value}\n")
        self.lex_tokens.config(state="disabled")

        for row in self.lex_symbol.get_children():
            self.lex_symbol.delete(row)
        for val in symbol_table.values():
            self.lex_symbol.insert("", "end", values=tuple(i for i in val.values()))
            
        for row in self.num_symbol.get_children():
            self.num_symbol.delete(row)
        for val in number_table.values():
            self.num_symbol.insert("", "end", values=tuple(i for i in val.values()))

        self.lex_error.config(state="normal")
        self.lex_error.delete("1.0", tk.END)
        self.lex_error.update()
        for err in lex_errors:
            self.lex_error.insert(tk.END, err+"\n-------------\n")
        self.lex_error.config(state="disabled")

    def _translate_asm(self):
        asm_mod = ASM()
        try:
            asm_mod.process(self.asm_src.get("1.0", "end"))
        except  (ASMLexicError, ASMParseError) as e:
            self.asm_out.configure(state="normal")
            self.asm_out.delete("1.0", "end")
            self.asm_out.insert("1.0", e)
            self.asm_out.configure(state="disabled")
        else:
            output = asm_mod.get_output()

            self.asm_out.configure(state="normal")
            self.asm_out.delete("1.0", "end")
            self.asm_out.insert("1.0", output)
            self.asm_out.configure(state="disabled")