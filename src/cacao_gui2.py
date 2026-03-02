"""
CACAO_Core-64 — Interfaz Gráfica Principal
==========================================
Panel de control del procesador simulado de 64 bits.
Coloca este archivo en src/ y ejecutalo con: python cacao_gui.py
"""

import tkinter as tk
from tkinter import messagebox
import subprocess, sys, os

# ── Importaciones del proyecto ─────────────────────────────────────────────
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from cacao_core import CacaoCore64
    BACKEND = "cacao_core.py OK"
except ImportError:
    CacaoCore64 = None
    BACKEND = "SIMULADO (cacao_core.py no encontrado)"

# ══════════════════════════════════════════════════════════════════════════════
#  PALETA — igual que cacao_ram_editor.py
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
BORDER    = "#2A3045"

FM       = ("Courier New", 11)
FM_SM    = ("Courier New",  9)
FM_LG    = ("Courier New", 14, "bold")
FM_XL    = ("Courier New", 20, "bold")
FM_TITLE = ("Courier New", 20, "bold")
FM_LABEL = ("Courier New", 10)
FM_BTN   = ("Courier New", 11, "bold")

# ══════════════════════════════════════════════════════════════════════════════
#  MOCK
# ══════════════════════════════════════════════════════════════════════════════
class _MockCU:
    def get_registers(self):
        d = {f"r{i}": i * 256 for i in range(13)}
        d.update({"sp": 0x000FFFFF, "lr": 0, "acc": 42,
                  "pc": 0x00001000, "ir": 0xDEADBEEFCAFEBABE,
                  "mar": 0x1000, "mdr": 0, "fr": 0b00000101, "dp": 0})
        return d

class _MockCore:
    def __init__(self):  self.processor = _MockCU()
    def boot(self, a):   pass
    def run_full(self):  pass
    def run_step(self):  pass

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════════════════════════
def make_panel(parent, title, color=ACCENT2, padx=10, pady=8):
    """Crea un frame con barra de titulo coloreada. Retorna el frame interior."""
    outer = tk.Frame(parent, bg=BORDER, bd=1, relief="flat")
    tk.Label(outer, text=f" {title} ", font=FM_SM,
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

# ══════════════════════════════════════════════════════════════════════════════
#  VENTANA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class CacaoCoreGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self._core = CacaoCore64() if CacaoCore64 else _MockCore()
        self._fmt  = tk.StringVar(value="hex")
        self._reg_labels   = {}
        self._flag_widgets = {}

        self.title("CACAO_Core-64  ·  Panel de Control")
        self.configure(bg=BG_DARK)
        self.minsize(1280, 800)
        self.resizable(True, True)
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-zoomed", True)

        self._build_header()
        self._build_body()
        self._build_statusbar()
        self.after(100, self._refresh_registers)

    # ─────────────────────────────────────────────────────────────────────
    #  HEADER
    # ─────────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_DARK, pady=10)
        hdr.pack(fill="x", padx=18, side="top")

        # Icono / logo pixelado
        canvas = tk.Canvas(hdr, width=40, height=40, bg=BG_DARK,
                           highlightthickness=0)
        canvas.pack(side="left", padx=(0, 10))
        for r in range(5):
            for c in range(5):
                if (r + c) % 2 == 0:
                    canvas.create_rectangle(c*8, r*8, c*8+7, r*8+7,
                                            fill=ACCENT, outline="")

        tk.Label(hdr, text="▓▓  CACAO_Core-64",
                 font=FM_TITLE, fg=ACCENT, bg=BG_DARK).pack(side="left")
        tk.Label(hdr, text="   PANEL DE CONTROL",
                 font=("Courier New", 14), fg=ACCENT2, bg=BG_DARK).pack(side="left")
        tk.Label(hdr, text=f"64-bit  ·  Von Neumann  ·  1 MB RAM   |   {BACKEND}",
                 font=FM_SM, fg=TEXT_DIM, bg=BG_DARK).pack(side="right")

        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x", padx=18, side="top")

    # ─────────────────────────────────────────────────────────────────────
    #  BODY — usa grid para control total de columnas
    # ─────────────────────────────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=18, pady=10, side="top")

        # 3 columnas: A fija, B fija, C expansible
        body.columnconfigure(0, minsize=300, weight=0)
        body.columnconfigure(1, minsize=440, weight=0)
        body.columnconfigure(2, weight=1)
        body.rowconfigure(0, weight=1)

        col_a = tk.Frame(body, bg=BG_DARK)
        col_a.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        col_b = tk.Frame(body, bg=BG_DARK)
        col_b.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

        col_c = tk.Frame(body, bg=BG_DARK)
        col_c.grid(row=0, column=2, sticky="nsew")

        # Columna A: control + formato (top), GPR (bottom, expand)
        col_a.rowconfigure(0, weight=0)
        col_a.rowconfigure(1, weight=0)
        col_a.rowconfigure(2, weight=1)
        col_a.columnconfigure(0, weight=1)

        ctrl_frame = tk.Frame(col_a, bg=BG_DARK)
        ctrl_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self._build_control_panel(ctrl_frame)

        fmt_frame = tk.Frame(col_a, bg=BG_DARK)
        fmt_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self._build_format_panel(fmt_frame)

        gpr_frame = tk.Frame(col_a, bg=BG_DARK)
        gpr_frame.grid(row=2, column=0, sticky="nsew")
        self._build_gpr_panel(gpr_frame)

        # Columna B: PC, IR, especiales, auxiliares
        col_b.rowconfigure(4, weight=1)
        col_b.columnconfigure(0, weight=1)
        self._build_pc_ir_panel(col_b)
        self._build_special_regs_panel(col_b)
        self._build_aux_regs_panel(col_b)

        # Columna C: flags + RAM
        col_c.rowconfigure(0, weight=0)
        col_c.rowconfigure(1, weight=1)
        col_c.columnconfigure(0, weight=1)
        self._build_flags_panel(col_c)
        self._build_ram_panel(col_c)

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA A: CONTROL DE EJECUCION
    # ─────────────────────────────────────────────────────────────────────
    def _build_control_panel(self, parent):
        outer, pf = make_panel(parent, "⚙  CONTROL DE EJECUCION", ACCENT2)
        outer.pack(fill="x")

        # Start Address
        sa_row = tk.Frame(pf, bg=BG_PANEL)
        sa_row.pack(fill="x", pady=(0, 8))

        tk.Label(sa_row, text="Start Address:", font=FM_LABEL,
                 fg=ACCENT4, bg=BG_PANEL).pack(side="left")
        tk.Label(sa_row, text="  0x", font=FM, fg=TEXT_DIM,
                 bg=BG_PANEL).pack(side="left")

        self._start_addr_var = tk.StringVar(value="00001000")
        tk.Entry(sa_row, textvariable=self._start_addr_var,
                 font=FM, bg=BG_INPUT, fg=ACCENT4,
                 insertbackground=ACCENT, relief="flat",
                 width=10, bd=4,
                 highlightthickness=1,
                 highlightcolor=ACCENT2,
                 highlightbackground=BORDER
                 ).pack(side="left", padx=2)

        tk.Frame(pf, bg=BORDER, height=1).pack(fill="x", pady=(0, 6))

        # Botones
        for label, color, cmd in [
            ("⚡  BOOT",       ACCENT,  self._do_boot),
            ("▶▶  RUN FULL",  ACCENT2, self._do_run_full),
            ("▶|  RUN STEP",  ACCENT5, self._do_run_step),
        ]:
            make_button(pf, label, color, cmd).pack(fill="x", pady=3)

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA A: FORMATO DE REGISTROS
    # ─────────────────────────────────────────────────────────────────────
    def _build_format_panel(self, parent):
        outer, pf = make_panel(parent, "◈  FORMATO DE REGISTROS", ACCENT4)
        outer.pack(fill="x")

        tk.Label(pf, text="Base numerica para todos los registros:",
                 font=FM_SM, fg=TEXT_DIM, bg=BG_PANEL, anchor="w").pack(fill="x", pady=(0, 6))

        row = tk.Frame(pf, bg=BG_PANEL)
        row.pack(fill="x")

        for val, lbl, color in [("hex","HEX",ACCENT4), ("dec","DEC",ACCENT2),
                                  ("bin","BIN",ACCENT5), ("oct","OCT",ACCENT)]:
            rb = tk.Radiobutton(
                row, text=lbl, variable=self._fmt, value=val,
                font=FM_BTN, fg=color, bg=BG_MID,
                selectcolor=color,
                activebackground=BG_MID, activeforeground=color,
                indicatoron=False, width=5, pady=6, relief="flat",
                cursor="hand2", command=self._refresh_registers
            )
            rb.pack(side="left", padx=3)

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA A: GPR r0-r12 (ocupa espacio restante)
    # ─────────────────────────────────────────────────────────────────────
    def _build_gpr_panel(self, parent):
        outer, pf = make_panel(parent, "█  REGISTROS GPR  (r0 – r12)", ACCENT, padx=6, pady=4)
        outer.pack(fill="both", expand=True)
        pf.pack_configure(fill="both", expand=True)

        canvas = tk.Canvas(pf, bg=BG_PANEL, highlightthickness=0)
        sb = tk.Scrollbar(pf, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        sf = tk.Frame(canvas, bg=BG_PANEL)
        win_id = canvas.create_window((0, 0), window=sf, anchor="nw")

        sf.bind("<Configure>", lambda e: (
            canvas.configure(scrollregion=canvas.bbox("all")),
            canvas.itemconfig(win_id, width=canvas.winfo_width())
        ))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

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
    #  COLUMNA B: PC e IR GRANDES
    # ─────────────────────────────────────────────────────────────────────
    def _build_pc_ir_panel(self, parent):
        for row_idx, (name, title, color) in enumerate([
            ("pc", "▸  PROGRAM COUNTER  [ PC ]", ACCENT),
            ("ir", "▸  INSTRUCTION REG  [ IR ]", ACCENT2),
        ]):
            outer, pf = make_panel(parent, title, color, padx=8, pady=6)
            outer.grid(row=row_idx, column=0, sticky="ew",
                       pady=(0, 6), padx=0)
            lbl = tk.Label(pf, text="0x0000000000000000",
                           font=FM_XL, fg=color, bg=BG_PANEL, anchor="center")
            lbl.pack(fill="x", pady=6)
            self._reg_labels[name] = lbl

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA B: SP, LR, ACC
    # ─────────────────────────────────────────────────────────────────────
    def _build_special_regs_panel(self, parent):
        outer, pf = make_panel(parent, "◉  REGISTROS ESPECIALES", ACCENT5)
        outer.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        for name, lbl_txt, color in [
            ("sp",  "$sp   Stack Pointer", ACCENT4),
            ("lr",  "$lr   Link Register", ACCENT2),
            ("acc", "$acc  Acumulador",    ACCENT),
        ]:
            row = tk.Frame(pf, bg=BG_PANEL)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=lbl_txt, font=FM_LABEL, fg=color,
                     bg=BG_PANEL, width=20, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="—", font=FM_LG, fg=TEXT_MAIN,
                           bg=BG_INPUT, anchor="e", relief="flat", padx=6)
            lbl.pack(side="left", fill="x", expand=True)
            self._reg_labels[name] = lbl

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA B: MAR, MDR, DP
    # ─────────────────────────────────────────────────────────────────────
    def _build_aux_regs_panel(self, parent):
        outer, pf = make_panel(parent,
                               "◈  REGISTROS INTERNOS  ( MAR · MDR · DP )",
                               BORDER)
        outer.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        row_f = tk.Frame(pf, bg=BG_PANEL)
        row_f.pack(fill="x")

        for name, lbl_txt, color in [
            ("mar", "MAR", ACCENT4),
            ("mdr", "MDR", ACCENT5),
            ("dp",  " DP", TEXT_DIM),
        ]:
            col = tk.Frame(row_f, bg=BG_PANEL)
            col.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(col, text=lbl_txt, font=FM_LABEL, fg=color,
                     bg=BG_PANEL, anchor="center").pack(fill="x")
            lbl = tk.Label(col, text="—", font=FM, fg=color,
                           bg=BG_INPUT, anchor="center",
                           relief="flat", padx=4, pady=3)
            lbl.pack(fill="x")
            self._reg_labels[name] = lbl

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA C: FLAGS REGISTER
    # ─────────────────────────────────────────────────────────────────────
    def _build_flags_panel(self, parent):
        outer, pf = make_panel(parent,
                               "⚑  FLAGS REGISTER  [ FR ]  —  little-endian",
                               ACCENT3)
        outer.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        # Valor raw
        raw_row = tk.Frame(pf, bg=BG_PANEL)
        raw_row.pack(fill="x", pady=(0, 10))
        tk.Label(raw_row, text="FR raw:", font=FM_LABEL,
                 fg=TEXT_DIM, bg=BG_PANEL, width=8, anchor="w").pack(side="left")
        self._fr_raw_lbl = tk.Label(raw_row,
                                    text="0x00   ·   0b00000000",
                                    font=FM, fg=ACCENT3, bg=BG_INPUT,
                                    anchor="w", padx=6, relief="flat")
        self._fr_raw_lbl.pack(side="left", fill="x", expand=True)

        # bit4=Z  bit3=N  bit2=C  bit1=V  bit0=I
        FLAG_DEFS = [
            (4, "Z", "Zero",      ACCENT),
            (3, "N", "Negative",  ACCENT3),
            (2, "C", "Carry",     ACCENT2),
            (1, "V", "Overflow",  ACCENT4),
            (0, "I", "Interrupt", ACCENT5),
        ]
        flags_row = tk.Frame(pf, bg=BG_PANEL)
        flags_row.pack(fill="x")

        for bit_idx, short, desc, color in FLAG_DEFS:
            col = tk.Frame(flags_row, bg=BG_PANEL,
                           highlightbackground=BORDER, highlightthickness=1)
            col.pack(side="left", expand=True, fill="both", padx=4, pady=2)

            tk.Label(col, text=short, font=("Courier New", 15, "bold"),
                     fg=color, bg=BG_PANEL).pack(pady=(8, 0))
            tk.Label(col, text=desc, font=FM_SM,
                     fg=TEXT_DIM, bg=BG_PANEL).pack()
            ind = tk.Label(col, text="0",
                           font=("Courier New", 28, "bold"),
                           fg=TEXT_DIM, bg=BG_MID,
                           width=3, pady=4)
            ind.pack(pady=(4, 4), fill="x")
            tk.Label(col, text=f"bit {bit_idx}", font=FM_SM,
                     fg=TEXT_DIM, bg=BG_PANEL).pack(pady=(0, 8))

            self._flag_widgets[bit_idx] = (ind, color)

    # ─────────────────────────────────────────────────────────────────────
    #  COLUMNA C: RAM EDITOR
    # ─────────────────────────────────────────────────────────────────────
    def _build_ram_panel(self, parent):
        outer, pf = make_panel(parent, "◈  MEMORIA RAM", ACCENT4)
        outer.grid(row=1, column=0, sticky="nsew")

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
    #  REFRESH
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

        # PC e IR siempre en HEX (son punteros/instrucciones)
        for name in ("pc", "ir"):
            lbl = self._reg_labels.get(name)
            if lbl:
                val = int(regs.get(name, 0)) & 0xFFFFFFFFFFFFFFFF
                lbl.config(text=f"0x{val:016X}")

        for name, bits in (("mar", 32), ("mdr", 48), ("dp", 8)):
            lbl = self._reg_labels.get(name)
            if lbl:
                lbl.config(text=self._fmt_val(regs.get(name, 0), bits))

        fr_val = int(regs.get("fr", 0)) & 0xFF
        self._fr_raw_lbl.config(text=f"0x{fr_val:02X}   ·   0b{fr_val:08b}")
        for bit_idx, (ind, color) in self._flag_widgets.items():
            bit_set = bool((fr_val >> bit_idx) & 1)
            ind.config(
                text="1" if bit_set else "0",
                fg=color  if bit_set else TEXT_DIM,
                bg=BG_PANEL if bit_set else BG_MID
            )

    # ─────────────────────────────────────────────────────────────────────
    #  ACCIONES
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
        if addr is None: return
        try:
            self._core.boot(addr)
            self._refresh_registers()
            self._set_status(f"BOOT completado  ·  PC -> 0x{addr:08X}", ACCENT)
        except Exception as e:
            self._set_status(f"ERROR en BOOT: {e}", ACCENT3)
            messagebox.showerror("Error de BOOT", str(e))

    def _do_run_full(self):
        try:
            self._core.run_full()
            self._refresh_registers()
            self._set_status("RUN FULL completado  ·  procesador detenido (HLT)", ACCENT2)
        except Exception as e:
            self._set_status(f"ERROR en RUN FULL: {e}", ACCENT3)
            messagebox.showerror("Error", str(e))

    def _do_run_step(self):
        try:
            self._core.run_step()
            self._refresh_registers()
            self._set_status("RUN STEP  ·  un ciclo fetch-decode-execute completado", ACCENT5)
        except Exception as e:
            self._set_status(f"ERROR en RUN STEP: {e}", ACCENT3)
            messagebox.showerror("Error", str(e))

    def _open_ram_editor(self):
        base = os.path.dirname(os.path.abspath(__file__))
        for p in [
            os.path.join(base, "memoria", "cacao_ram_editor.py"),
            os.path.join(base, "cacao_ram_editor.py"),
        ]:
            if os.path.exists(p):
                subprocess.Popen([sys.executable, p])
                self._set_status("RAM Editor abierto.", ACCENT4)
                return
        messagebox.showinfo("RAM Editor",
            "No se encontro cacao_ram_editor.py\n"
            "Ruta esperada: src/memoria/cacao_ram_editor.py")

    def _set_status(self, msg, color=ACCENT):
        self._status_var.set(f"  {msg}")
        self._status_lbl.config(fg=color)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = CacaoCoreGUI()
    app.mainloop()
