import tkinter as tk
from tkinter import filedialog
from gui.color_palette import *
from assembler import ASM


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

        self.index          = 0          # fase activa (0-3)
        self.compiler_step  = 0          # sub-paso del compilador (0=léxico, 1=sintáctico, 2=semántico)

        self._create_body()
        self._setup_header()
        self._setup_body()
        self._set_menu()
        self._pre_compiler()             # fase inicial

    # ══════════════════════════════════════════════════════════════════════
    # ESTRUCTURA BASE
    # ══════════════════════════════════════════════════════════════════════

    def _create_body(self):
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=0)
        self.window.grid_rowconfigure(2, weight=4)
        self.window.grid_rowconfigure(3, weight=40)
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

        phases  = ["Pre-Compiler", "Compiler", "Assembler", "Loader / Linker"]
        colors  = [ACCENT, ACCENT2, ACCENT3, ACCENT4]
        cmds    = [self._pre_compiler, self._compiler, self._assembler, self._link_load]

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

        phase_names = ["Pre-Compiler", "Compiler", "Assembler", "Loader / Linker"]
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
        # Reset grid configs
        for r in range(10):
            self.content.grid_rowconfigure(r, weight=0)
        for c in range(10):
            self.content.grid_columnconfigure(c, weight=0)

    def _scrollable_text(self, parent, fg=TEXT_MAIN, state="normal", font=None):
        """Devuelve un Text con scrollbar vertical dentro de parent (que debe tener grid listo)."""
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

    # ══════════════════════════════════════════════════════════════════════
    # FASE 0 – PRE-COMPILER
    # ══════════════════════════════════════════════════════════════════════

    def _pre_compiler(self):
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

        self._section_label(right, "◈  PRE-COMPILED OUTPUT", ACCENT
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))

        tf_r, self.pc_out = self._scrollable_text(right, fg=ACCENT, state="disabled")
        tf_r.grid(row=1, column=0, sticky="nsew")

        # ── Barra de botones ─────────────────────────────────────────────
        btn_bar = tk.Frame(self.content, bg=BG_PANEL)
        btn_bar.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        self._action_btn(btn_bar, "⚙  Pre-compile", ACCENT,
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

    def _compiler(self):
        self.compiler_step = 0
        self._build_compiler_step()

    def _build_compiler_step(self):
        self._clear_content()

        self.content.grid_rowconfigure(0, weight=0)   # nav bar
        self.content.grid_rowconfigure(1, weight=1)   # área principal
        self.content.grid_rowconfigure(2, weight=0)   # botones
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

        # Deshabilitar flechas en extremos
        if self.compiler_step == 0:
            self.btn_prev.configure(state="disabled", bg=BG_MID)
        if self.compiler_step == 2:
            self.btn_next.configure(state="disabled", bg=BG_MID)

        # ── Contenido del paso ───────────────────────────────────────────
        area = tk.Frame(self.content, bg=BG_PANEL)
        area.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)
        area.grid_columnconfigure(1, weight=1)

        if self.compiler_step == 0:
            self._build_lexical(area)
        elif self.compiler_step == 1:
            self._build_syntactic(area)
        else:
            self._build_semantic(area)

    # ── Paso 0: Léxico ────────────────────────────────────────────────────

    def _build_lexical(self, area):
        # Izquierda: código precompilado
        left = tk.Frame(area, bg=BG_PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._section_label(left, "◈  PRE-COMPILED INPUT", ACCENT2
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))
        tf_l, self.lex_input = self._scrollable_text(left)
        tf_l.grid(row=1, column=0, sticky="nsew")

        # Derecha: tokens
        right = tk.Frame(area, bg=BG_PANEL)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._section_label(right, "◈  TOKENS IDENTIFIED", ACCENT4
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))
        tf_r, self.lex_tokens = self._scrollable_text(right, fg=ACCENT4, state="disabled", font=FM_SM)
        tf_r.grid(row=1, column=0, sticky="nsew")

        # Botón
        btn_bar = tk.Frame(self.content, bg=BG_PANEL)
        btn_bar.grid(row=2, column=0, pady=(0, 10))
        self._action_btn(btn_bar, "⚙  Start Lexical Analysis", ACCENT2,
                         self._do_lexical).pack()

    # ── Paso 1: Sintáctico (vacío) ────────────────────────────────────────

    def _build_syntactic(self, area):
        tk.Label(area, text="[ Syntactic Analysis — coming soon ]",
                 bg=BG_PANEL, fg=TEXT_DIM, font=FM_LG
                 ).grid(row=0, column=0, columnspan=2, pady=40)

    # ── Paso 2: Semántico (vacío) ─────────────────────────────────────────

    def _build_semantic(self, area):
        tk.Label(area, text="[ Semantic Analysis — coming soon ]",
                 bg=BG_PANEL, fg=TEXT_DIM, font=FM_LG
                 ).grid(row=0, column=0, columnspan=2, pady=40)

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

    def _assembler(self):
        self._clear_content()

        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=0)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=0)   # botón central
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

        # ── Centro: botón TRANSLATE ──────────────────────────────────────
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
        
        self._action_btn(btn_bar, "▶ TRANSLATE", ACCENT,
                  self._translate_asm
                  ).pack(side="left", padx=10)
        
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

    def _link_load(self):
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

        # ── Derecha: código cargado en memoria ───────────────────────────
        right = tk.Frame(self.content, bg=BG_PANEL)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._section_label(right, "◈  MEMORY-LOADED CODE", ACCENT
                            ).grid(row=0, column=0, sticky="ew", pady=(4, 2))

        # Entry dirección base
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
        self.ll_base_addr.insert(0, "0000")

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
        """Placeholder – conectar lógica de link & load aquí."""
        pass

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
    # NAVEGACION
    # ══════════════════════════════════════════════════════════════════════

    def _next_phase(self):
        cmds = [self._pre_compiler, self._compiler, self._assembler, self._link_load]
        if self.index < len(cmds) - 1:
            self.index += 1
            self._set_menu()
            cmds[self.index]()



    # ══════════════════════════════════════════════════════════════════════
    # FUNC QUE REQUIEREN COMPILER
    # ══════════════════════════════════════════════════════════════════════

    def _do_precompile(self):
        """Placeholder – conectar lógica de precompilación aquí."""
        self.pc_hl #entrada con el high level language
        self.pc_out #salida con el precompiled output
        pass

    def _do_lexical(self):
        """Esta funcion es llamada cuando hacemos el lexico el entry con el texto del lexico es self.lex_input y la salida es self.lex_tokens
        Los metodos de los text son .get("1.0", "end") para tarer todo lo de un text desde la linea 1 caracter 0
        .delete() para borrar el text y el insert para cargarlo, las operaciones son permitidas siempre que su state este normal"""
        self.lex
        pass

    def _translate_asm(self):
        asm_mod = ASM()
        asm_mod.process(self.asm_src.get("1.0", "end"))

        output = asm_mod.get_output()

        self.asm_out.configure(state="normal")
        self.asm_out.delete("1.0", "end")
        self.asm_out.insert("1.0", output)
        self.asm_out.configure(state="disabled") 

    

    