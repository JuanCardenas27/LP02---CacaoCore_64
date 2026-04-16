import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from gui.styles_spl import *
from assembler import ASM
from compiler import compiler
from preprocesador.preprocesador import Preprocesador, PreprocesadorError


class CompilerGui:
    def __init__(self, master):
        self.window = tk.Toplevel(master, bg=BG_DARK)
        self.window.title("Language Processing")

        width  = int(self.window.winfo_screenwidth()  * 0.98)
        height = int(self.window.winfo_screenheight() * 0.9)
        self.window.geometry(f"{width}x{height}+0+0")
        self.window.resizable(False, False)
        self.window.lift()
        self.window.focus_force()
        self.window.grab_set()

        self.index           = 0
        self.compiler_step   = 0
        self._carry_compiler = ""   # texto que viaja de pre-processor → compiler
        self._carry_loader   = ""   # texto que viaja de assembler     → link&load

        # Incializa estilos 
        setup_styles()

        self._create_body()
        self._setup_header()
        self._setup_body()
        self._set_menu()
        self._pre_compiler()

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

        tk.Label(hdr, text="CACAO_Core-64",
                 font=FM_TITLE, fg=ACCENT, bg=BG_DARK).pack(side="left")
        tk.Label(hdr, text="   LANGUAGE PROCESSOR SYSTEM",
                 font=("Courier New", 14), fg=ACCENT2, bg=BG_DARK).pack(side="left")
        tk.Label(hdr, text="64-bit  ·  Von Neumann  ·  1 MB RAM",
                 font=FM_SM, fg=TEXT_DIM, bg=BG_DARK).pack(side="right")

        tk.Frame(self.window, bg=ACCENT, height=2).grid(row=1, column=0, sticky="ew")

    def _setup_header(self):
        self.header.grid_rowconfigure(0, weight=1)
        self.header.grid_columnconfigure(0, weight=1)

        panel = tk.Frame(self.header, bg=BG_PANEL,
                         highlightbackground=BORDER, highlightthickness=2)
        panel.grid(row=0, column=0)

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
            btn.grid(row=0, column=i, padx=5, pady=5)
            self._phase_btns.append(btn)

    def _switch_phase(self, cmd, idx):
        """Botones del header: navegan sin carry (acceso directo)."""
        self.index = idx
        self._set_menu()
        cmd()

    def _setup_body(self):
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_columnconfigure(1, weight=0)

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

    def _pc_load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All", "*.*")])
        self.window.lift()
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.pc_hl.delete("1.0", tk.END)
            self.pc_hl.insert("1.0", data)

    def _pc_erase(self):
        self.pc_hl.delete("1.0", tk.END)
        self.pc_out.configure(state="normal")
        self.pc_out.delete("1.0", tk.END)
        self.pc_out.configure(state="disabled")

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
        right.grid_rowconfigure(3, weight=4)
        right.grid_columnconfigure(0, weight=1)

        self._section_label(right, "◈  Symbol Table", ACCENT4
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))
        columns = ['Lexeme', 'Length', 'Lines', 'Kind', 'Type', 'Value', 'Scope']
        tf_r, self.lex_symbol = self._scrollable_table(right, columns)
        tf_r.grid(row=1, column=0, sticky="nsew")
        tf_r.grid(row=1, column=0, sticky="nsew")

        self._section_label(right, "◈  Errores", ACCENT5
                            ).grid(row=2, column=0, sticky="ew", pady=(4, 2))
        tf_e, self.lex_error = self._scrollable_text(right, fg=ACCENT5, state="disabled", font=FM_SM)
        tf_e.grid(row=3, column=0, sticky="nsew")

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

    def _asm_load(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All", "*.*")])
        self.window.lift()
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.asm_src.delete("1.0", tk.END)
            self.asm_src.insert("1.0", data)

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

    def _do_link_load(self):
        """
        Procesa el código relocalizable y lo carga en memoria usando el enlazador.
        
        El formato reloc es:
        .data
        <hex bytes>
        .text
        <hex bytes con referencias [x] y {x}>
        """
        try:
            # Obtener el contenido del reloc
            reloc_content = self.ll_reloc.get("1.0", tk.END).strip()
            if not reloc_content:
                self._show_error("Error", "No hay código relocalizable para procesar")
                return
            
            # Obtener dirección base
            base_addr_hex = self.ll_base_addr.get().strip()
            if not base_addr_hex:
                self._show_error("Error", "Dirección base vacía")
                return
            
            try:
                base_addr = int(base_addr_hex, 16)
            except ValueError:
                self._show_error("Error", f"Dirección base inválida: {base_addr_hex}")
                return
            
            # Parsear el formato reloc
            parsed = self._parse_reloc_format(reloc_content)
            
            if parsed is None:
                self._show_error("Error", "Formato de reloc inválido")
                return
            
            data_hex, text_hex = parsed
            
            # Convertir a módulo objeto para el enlazador
            module_obj = self._create_obj_module(data_hex, text_hex, base_addr)
            
            if module_obj is None:
                self._show_error("Error", "No se pudo crear el módulo objeto")
                return
            
            # Usar el gestor de enlazador-cargador
            from enlazador_cargador.gestor_enlazador_cargador import GestorEnlazadorCargador
            from memoria.ram import ram
            
            gestor = GestorEnlazadorCargador(verbose=False)
            
            # Cargar y enlazar
            exito = gestor.cargar_desde_contenido(
                {'programa': module_obj},
                direccion_base=base_addr,
                cargar_en_memoria=True
            )
            
            if not exito:
                self._show_error("Error de carga", 
                    f"Error al cargar: {gestor.obtener_ultimo_error()}")
                return
            
            # Mostrar resultado en la interfaz
            self._show_loaded_code(base_addr, data_hex, text_hex)
            
            # Opcional: mostrar tabla de símbolos
            tabla = gestor.obtener_tabla_simbolos()
            if tabla:
                simbolos_str = "\n".join([f"{nom}: 0x{sym.valor:X}" 
                    for nom, sym in tabla.items()])
                self.ll_loaded.configure(state="normal")
                self.ll_loaded.insert(tk.END, f"\n\n=== Símbolos ===\n{simbolos_str}")
                self.ll_loaded.configure(state="disabled")
            
            self._show_message("Éxito", "Código cargado en memoria exitosamente")
            
        except Exception as e:
            self._show_error("Error inesperado", f"{type(e).__name__}: {e}")
    
    def _parse_reloc_format(self, content):
        """
        Parsea el formato reloc:
        .data
        <hex>
        .text
        <hex>
        
        Retorna: (data_hex, text_hex) o None si hay error
        """
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        
        data_hex = ""
        text_hex = ""
        section = None
        
        for line in lines:
            if line == ".data":
                section = "data"
                continue
            elif line == ".text":
                section = "text"
                continue
            
            if section == "data":
                # Procesar línea de datos
                hex_str = self._process_reloc_line(line)
                if hex_str:
                    data_hex += hex_str
            elif section == "text":
                # Procesar línea de texto
                hex_str = self._process_reloc_line(line)
                if hex_str:
                    text_hex += hex_str
        
        if not data_hex and not text_hex:
            return None
        
        return (data_hex, text_hex)
    
    def _process_reloc_line(self, line):
        """
        Procesa una línea de reloc, reemplazando referencias como:
        - {9} → bytes para referencia
        - [2] → bytes para referencia
        
        Por ahora, convierte referencias a ceros (placeholder).
        """
        import re
        
        # Reemplazar referencias con ceros (serán procesadas por el enlazador)
        line = re.sub(r'\{[0-9]+\}', '00', line)  # {9} → 00
        line = re.sub(r'\[[0-9]+\]', '00', line)  # [2] → 00
        line = re.sub(r'\[[0-9]+\]', '00', line)  # 1[2]8 → 100008 (el 1[2]8)
        
        # Eliminar espacios y convertir a hex válido
        line = line.replace(' ', '').replace('\t', '')
        
        # Validar que sean caracteres hex válidos
        if not all(c in '0123456789ABCDEFabcdef' for c in line):
            return ""
        
        return line
    
    def _create_obj_module(self, data_hex, text_hex, base_addr):
        """
        Crea un módulo objeto compatible con el enlazador.
        
        Formato:
        [MODULE nombre]
        [CODE] hex_bytes
        [DATA] hex_bytes
        [SYMBOLS] nombre:tipo:valor
        [EXTERNAL]
        """
        # Convertir strings hex a formato espaciado para el módulo objeto
        code_formatted = self._format_hex_for_module(text_hex)
        data_formatted = self._format_hex_for_module(data_hex)
        
        module = f"""[MODULE programa]
[CODE] {code_formatted}
[DATA] {data_formatted}
[SYMBOLS] inicio:code:0x{base_addr:X}
[EXTERNAL]
"""
        return module
    
    def _format_hex_for_module(self, hex_string):
        """Formatea un string hex para el módulo objeto (XX XX XX XX ...)"""
        if not hex_string:
            return ""
        
        # Agrupar en pares
        hex_string = hex_string.replace(' ', '')
        pairs = [hex_string[i:i+2].upper() for i in range(0, len(hex_string), 2)]
        return ' '.join(pairs)
    
    def _show_loaded_code(self, base_addr, data_hex, text_hex):
        """Muestra el código cargado en el widget ll_loaded"""
        self.ll_loaded.configure(state="normal")
        self.ll_loaded.delete("1.0", tk.END)
        
        output = f"BASE ADDRESS: 0x{base_addr:08X}\n"
        output += f"===============================\n\n"
        
        if data_hex:
            output += f"DATA SECTION (0x{base_addr:08X}):\n"
            # Mostrar en filas de 8 bytes
            for i in range(0, len(data_hex), 16):
                output += data_hex[i:i+16] + "\n"
            output += f"\n"
        
        if text_hex:
            output += f"CODE SECTION (0x{base_addr + len(data_hex)//2:08X}):\n"
            # Mostrar en filas de 8 bytes
            for i in range(0, len(text_hex), 16):
                output += text_hex[i:i+16] + "\n"
        
        self.ll_loaded.insert(tk.END, output)
        self.ll_loaded.configure(state="disabled")
    
    def _show_error(self, title, message):
        """Muestra un diálogo de error"""
        from tkinter import messagebox
        messagebox.showerror(title, message)
    
    def _show_message(self, title, message):
        """Muestra un diálogo informativo"""
        from tkinter import messagebox
        messagebox.showinfo(title, message)
    

    def _ll_load(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All", "*.*")])
        self.window.lift()
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.ll_reloc.delete("1.0", tk.END)
            self.ll_reloc.insert("1.0", data)

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
            resultado = pre.preprocess(codigo, nombre_fuente="<gui>")
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

        self.lex_tokens.config(state="normal")
        self.lex_tokens.delete("1.0", tk.END)
        for tkn in tokens:
            self.lex_tokens.insert(tk.END, f"{tkn.type}: {tkn.value}\n")
        self.lex_tokens.config(state="disabled")

        for row in self.lex_symbol.get_children():
            self.lex_symbol.delete(row)
        for val in symbol_table.values():
            self.lex_symbol.insert("", "end", values=tuple(i for i in val.values()))

        self.lex_error.config(state="normal")
        self.lex_error.delete("1.0", tk.END)
        self.lex_error.update()
        for err in lex_errors:
            self.lex_error.insert(tk.END, err+"\n-------------\n")
        self.lex_error.config(state="disabled")

    def _translate_asm(self):
        asm_mod = ASM()
        asm_mod.process(self.asm_src.get("1.0", "end"))
        output = asm_mod.get_output()

        self.asm_out.configure(state="normal")
        self.asm_out.delete("1.0", "end")
        self.asm_out.insert("1.0", output)
        self.asm_out.configure(state="disabled")