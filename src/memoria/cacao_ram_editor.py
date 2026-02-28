"""
CACAO_Core-64 — Editor Directo de RAM
Tarea 14: Frontend para escritura directa sobre la memoria RAM
Arquitectura: Von Neumann, 64 bits, 1 MB RAM, direcciones 32 bits

"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re

# ─────────────────────────────────────────────
#  IMPORTAR LA RAM REAL DESDE ram.py
# ─────────────────────────────────────────────
try:
    from ram import (
        ram,
        RAM_SIZE,
        WORD_SIZE,
        SYS_START, SYS_END,
        CODE_START, CODE_END,
        DATA_START, DATA_END,
        HEAP_START, HEAP_END,
        STACK_START, STACK_END,
        RAMError,
        AddressOutOfRange,
        AlignmentError,
        WriteProtectionError,
    )
    RAM_BACKEND = "ram.py"
except ImportError:
    # Fallback: si ram.py no está disponible, usa bytearray directo
    RAM_SIZE  = 1 * 1024 * 1024
    WORD_SIZE = 8
    ram       = type("_FakeRAM", (), {
        "_mem":            bytearray(RAM_SIZE),
        "write":           lambda self, a, d: self._mem.__setitem__(slice(a, a+len(d)), d),
        "read":            lambda self, a, n: bytes(self._mem[a:a+n]),
        "code_protected":  False,
        "zone_of":         lambda self, a: "N/A",
    })()
    SYS_START, SYS_END       = 0x00000000, 0x00001000
    CODE_START, CODE_END     = 0x00001000, 0x00040000
    DATA_START, DATA_END     = 0x00040000, 0x00080000
    HEAP_START, HEAP_END     = 0x00080000, 0x000C0000
    STACK_START, STACK_END   = 0x000C0000, 0x00100000
    RAMError = WriteProtectionError = AddressOutOfRange = AlignmentError = Exception
    RAM_BACKEND = "fallback (ram.py no encontrado)"

# ─────────────────────────────────────────────
#  MAPA VISUAL (colores por zona)
# ─────────────────────────────────────────────
MEMORY_MAP = [
    (SYS_START,   SYS_END   - 1, "Sistema / Vectores",  "#FF6B6B"),
    (CODE_START,  CODE_END  - 1, "Código del programa", "#4ECDC4"),
    (DATA_START,  DATA_END  - 1, "Datos estáticos",     "#FFE66D"),
    (HEAP_START,  HEAP_END  - 1, "Heap",                "#A8E6CF"),
    (STACK_START, STACK_END - 1, "Pila (Stack)",        "#C3A6FF"),
]

REGISTERS = [
    ("$r0–$r12", "0000–1100", "Propósito general"),
    ("$sp",      "1101",      "Stack Pointer"),
    ("$lr",      "1110",      "Link Register"),
    ("$acc",     "1111",      "Acumulador"),
]

ADDR_MODE_BITS = {"Registro": "00", "Inmediato": "01", "Mem. Directa": "10", "Mem. Indirecta": "11"}

# Paleta de colores retro-terminal
BG_DARK    = "#0D0F12"
BG_MID     = "#141720"
BG_PANEL   = "#1A1D28"
BG_INPUT   = "#0A0C10"
ACCENT     = "#00FF9C"
ACCENT2    = "#00C8FF"
ACCENT3    = "#FF6B6B"
TEXT_MAIN  = "#E0E8F0"
TEXT_DIM   = "#5A6880"
TEXT_ADDR  = "#FFD166"
BORDER     = "#2A3045"
FONT_MONO  = ("Courier New", 11)
FONT_MONO_SM = ("Courier New", 9)
FONT_TITLE = ("Courier New", 18, "bold")
FONT_LABEL = ("Courier New", 10)
FONT_SMALL = ("Courier New", 9)

# ─────────────────────────────────────────────
#  HELPERS — usan la instancia `ram` de ram.py
# ─────────────────────────────────────────────
def get_segment(addr):
    for start, end, name, color in MEMORY_MAP:
        if start <= addr <= end:
            return name, color
    return "Desconocido", "#888888"

def write_ram(addr, data_bytes):
    """
    Escribe bytes en la RAM usando ram.write().
    Delega todas las validaciones (bounds, protección) a ram.py.
    Retorna (ok: bool, mensaje: str).
    """
    try:
        ram.write(addr, bytes(data_bytes))
        return True, f"OK — {len(data_bytes)} byte(s) escritos en 0x{addr:08X}"
    except WriteProtectionError as e:
        return False, f"Zona protegida: {e}"
    except AddressOutOfRange as e:
        return False, f"Fuera de rango: {e}"
    except RAMError as e:
        return False, f"Error de RAM: {e}"
    except Exception as e:
        return False, str(e)

def read_ram(addr, length):
    """
    Lee bytes desde la RAM usando ram.read().
    Retorna (data: bytes, mensaje: str).
    """
    try:
        return ram.read(addr, length), "OK"
    except RAMError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────────
#  APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────────
class CacaoRAMEditor(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("CACAO_Core-64  ·  Editor de RAM")
        self.geometry("1260x820")
        self.minsize(1100, 700)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        self._build_ui()
        self._refresh_hex_view(0x00001000, 16)

    # ─── UI PRINCIPAL ─────────────────────────────
    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=BG_DARK, pady=8)
        hdr.pack(fill="x", padx=16)

        tk.Label(hdr, text="▓▓  CACAO_Core-64", font=FONT_TITLE,
                 fg=ACCENT, bg=BG_DARK).pack(side="left")
        tk.Label(hdr, text="  RAM DIRECT EDITOR", font=("Courier New", 13),
                 fg=ACCENT2, bg=BG_DARK).pack(side="left", padx=8)
        tk.Label(hdr, text=f"1 MB · 32-bit addr · 64-bit word  │  backend: {RAM_BACKEND}",
                 font=FONT_SMALL, fg=TEXT_DIM, bg=BG_DARK).pack(side="right")

        sep = tk.Frame(self, bg=ACCENT, height=1)
        sep.pack(fill="x", padx=16)

        # ── Cuerpo ──
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=8)

        # Columna izquierda: controles
        left = tk.Frame(body, bg=BG_DARK, width=420)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self._build_write_panel(left)
        self._build_read_panel(left)
        self._build_memmap_panel(left)
        self._build_regref_panel(left)

        # Columna derecha: visor hex + log
        right = tk.Frame(body, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)

        self._build_hex_viewer(right)
        self._build_log(right)

    # ─── PANEL: ESCRITURA ─────────────────────────
    def _build_write_panel(self, parent):
        f = self._panel(parent, "✎  ESCRIBIR EN RAM")

        # Dirección
        row1 = tk.Frame(f, bg=BG_PANEL)
        row1.pack(fill="x", pady=3)
        tk.Label(row1, text="Dirección (hex):", font=FONT_LABEL,
                 fg=TEXT_ADDR, bg=BG_PANEL, width=18, anchor="w").pack(side="left")
        self.addr_var = tk.StringVar(value="00001000")
        addr_e = tk.Entry(row1, textvariable=self.addr_var, font=FONT_MONO,
                          bg=BG_INPUT, fg=TEXT_ADDR, insertbackground=ACCENT,
                          relief="flat", width=12, bd=4)
        addr_e.pack(side="left", padx=4)
        tk.Label(row1, text="0x", font=FONT_MONO, fg=TEXT_DIM, bg=BG_PANEL).pack(side="left")

        # Datos
        row2 = tk.Frame(f, bg=BG_PANEL)
        row2.pack(fill="x", pady=3)
        tk.Label(row2, text="Datos:", font=FONT_LABEL,
                 fg=TEXT_MAIN, bg=BG_PANEL, width=18, anchor="w").pack(side="left")

        self.data_mode = tk.StringVar(value="hex")
        for val, lbl in [("hex","HEX"), ("bin","BIN"), ("dec","DEC")]:
            rb = tk.Radiobutton(row2, text=lbl, variable=self.data_mode, value=val,
                                font=FONT_SMALL, fg=ACCENT2, bg=BG_PANEL,
                                selectcolor=BG_INPUT, activebackground=BG_PANEL,
                                activeforeground=ACCENT2, indicatoron=True,
                                command=self._update_data_placeholder)
            rb.pack(side="left", padx=4)

        # Caja de datos
        self.data_text = tk.Text(f, font=FONT_MONO, bg=BG_INPUT, fg=ACCENT,
                                  insertbackground=ACCENT, relief="flat",
                                  height=3, bd=6, wrap="word")
        self.data_text.pack(fill="x", pady=4)
        self.data_text.insert("1.0", "FF 00 1A 2B 3C 4D 5E 6F")

        # Info de segmento
        self.seg_label = tk.Label(f, text="", font=FONT_SMALL,
                                   bg=BG_PANEL, fg=TEXT_DIM, anchor="w")
        self.seg_label.pack(fill="x")
        self.addr_var.trace_add("write", self._update_seg_label)
        self._update_seg_label()

        # Botón escribir
        btn = tk.Button(f, text="▶  ESCRIBIR", font=("Courier New", 11, "bold"),
                        bg=ACCENT, fg=BG_DARK, relief="flat", pady=6,
                        activebackground="#00CC7A", activeforeground=BG_DARK,
                        cursor="hand2", command=self._do_write)
        btn.pack(fill="x", pady=(8, 4))

        # Control de protección de zona de código
        prot_row = tk.Frame(f, bg=BG_PANEL)
        prot_row.pack(fill="x", pady=(2, 0))
        tk.Label(prot_row, text="Zona código:", font=FONT_SMALL,
                 fg=TEXT_DIM, bg=BG_PANEL).pack(side="left")
        self.prot_label = tk.Label(prot_row, text="", font=("Courier New", 9, "bold"),
                                    bg=BG_PANEL)
        self.prot_label.pack(side="left", padx=6)
        self._refresh_prot_label()
        tk.Button(prot_row, text=" Proteger", font=FONT_SMALL,
                  bg="#2A3045", fg=ACCENT3, relief="flat", padx=6,
                  cursor="hand2",
                  command=self._protect_code).pack(side="right", padx=(4, 0))
        tk.Button(prot_row, text=" Desproteger", font=FONT_SMALL,
                  bg="#2A3045", fg=ACCENT, relief="flat", padx=6,
                  cursor="hand2",
                  command=self._unprotect_code).pack(side="right")

    # ─── PANEL: LECTURA ──────────────────────────
    def _build_read_panel(self, parent):
        f = self._panel(parent, "◉  LEER DESDE RAM")

        row = tk.Frame(f, bg=BG_PANEL)
        row.pack(fill="x", pady=3)
        tk.Label(row, text="Dirección (hex):", font=FONT_LABEL,
                 fg=TEXT_ADDR, bg=BG_PANEL, width=18, anchor="w").pack(side="left")
        self.read_addr_var = tk.StringVar(value="00001000")
        tk.Entry(row, textvariable=self.read_addr_var, font=FONT_MONO,
                 bg=BG_INPUT, fg=TEXT_ADDR, insertbackground=ACCENT,
                 relief="flat", width=12, bd=4).pack(side="left", padx=4)

        row2 = tk.Frame(f, bg=BG_PANEL)
        row2.pack(fill="x", pady=3)
        tk.Label(row2, text="Bytes a leer:", font=FONT_LABEL,
                 fg=TEXT_MAIN, bg=BG_PANEL, width=18, anchor="w").pack(side="left")
        self.read_len_var = tk.StringVar(value="16")
        tk.Entry(row2, textvariable=self.read_len_var, font=FONT_MONO,
                 bg=BG_INPUT, fg=TEXT_MAIN, insertbackground=ACCENT,
                 relief="flat", width=6, bd=4).pack(side="left", padx=4)

        btn_frame = tk.Frame(f, bg=BG_PANEL)
        btn_frame.pack(fill="x", pady=(6, 2))
        tk.Button(btn_frame, text="◉  LEER", font=("Courier New", 10, "bold"),
                  bg=ACCENT2, fg=BG_DARK, relief="flat", pady=5,
                  activebackground="#009FCC", activeforeground=BG_DARK,
                  cursor="hand2", command=self._do_read).pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(btn_frame, text="⟳  VER HEX", font=("Courier New", 10, "bold"),
                  bg="#2A3045", fg=TEXT_MAIN, relief="flat", pady=5,
                  activebackground="#3A4060", activeforeground=ACCENT,
                  cursor="hand2", command=self._do_refresh_hex).pack(side="left", fill="x", expand=True)

    # ─── PANEL: MAPA DE MEMORIA ───────────────────
    def _build_memmap_panel(self, parent):
        f = self._panel(parent, "⬡  MAPA DE MEMORIA")
        for start, end, name, color in MEMORY_MAP:
            row = tk.Frame(f, bg=BG_PANEL, pady=1)
            row.pack(fill="x")
            dot = tk.Label(row, text="●", font=FONT_SMALL, fg=color, bg=BG_PANEL, width=2)
            dot.pack(side="left")
            addr_txt = f"0x{start:08X}–0x{end:08X}"
            tk.Label(row, text=addr_txt, font=FONT_MONO_SM,
                     fg=TEXT_ADDR, bg=BG_PANEL, width=22, anchor="w").pack(side="left")
            tk.Label(row, text=name, font=FONT_SMALL,
                     fg=TEXT_MAIN, bg=BG_PANEL).pack(side="left", padx=4)
            # botón ir
            tk.Button(row, text="→", font=FONT_SMALL,
                      bg=BG_MID, fg=color, relief="flat", padx=4,
                      cursor="hand2",
                      command=lambda s=start: self._jump_to(s)).pack(side="right")

    # ─── PANEL: REFERENCIA DE REGISTROS ──────────
    def _build_regref_panel(self, parent):
        f = self._panel(parent, "⊞  REGISTROS (referencia)")
        hdr_row = tk.Frame(f, bg=BG_PANEL)
        hdr_row.pack(fill="x")
        for h, w in [("Símbolo", 12), ("Cod.", 6), ("Rol", 20)]:
            tk.Label(hdr_row, text=h, font=("Courier New", 9, "bold"),
                     fg=ACCENT2, bg=BG_PANEL, width=w, anchor="w").pack(side="left")

        sep = tk.Frame(f, bg=BORDER, height=1)
        sep.pack(fill="x", pady=2)

        for sym, cod, rol in REGISTERS:
            row = tk.Frame(f, bg=BG_PANEL)
            row.pack(fill="x")
            tk.Label(row, text=sym, font=FONT_MONO_SM, fg=ACCENT, bg=BG_PANEL, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=cod,  font=FONT_MONO_SM, fg=TEXT_ADDR, bg=BG_PANEL, width=6,  anchor="w").pack(side="left")
            tk.Label(row, text=rol,  font=FONT_SMALL,   fg=TEXT_MAIN, bg=BG_PANEL, width=20, anchor="w").pack(side="left")

    # ─── VISOR HEXADECIMAL ────────────────────────
    def _build_hex_viewer(self, parent):
        lbl = tk.Label(parent, text="⬡  VISOR HEXADECIMAL DE RAM",
                       font=("Courier New", 10, "bold"), fg=ACCENT2,
                       bg=BG_DARK, anchor="w")
        lbl.pack(fill="x", pady=(0, 4))

        viewer_frame = tk.Frame(parent, bg=BG_PANEL, bd=0)
        viewer_frame.pack(fill="both", expand=True)

        # Barra superior del visor
        top = tk.Frame(viewer_frame, bg=BG_MID, pady=4, padx=8)
        top.pack(fill="x")

        tk.Label(top, text="Base addr:", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_MID).pack(side="left")
        self.hex_base_var = tk.StringVar(value="00001000")
        tk.Entry(top, textvariable=self.hex_base_var, font=FONT_MONO,
                 bg=BG_INPUT, fg=TEXT_ADDR, insertbackground=ACCENT,
                 relief="flat", width=10, bd=3).pack(side="left", padx=6)
        tk.Label(top, text="Rows:", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_MID).pack(side="left")
        self.hex_rows_var = tk.StringVar(value="16")
        tk.Entry(top, textvariable=self.hex_rows_var, font=FONT_MONO,
                 bg=BG_INPUT, fg=TEXT_MAIN, insertbackground=ACCENT,
                 relief="flat", width=5, bd=3).pack(side="left", padx=4)
        tk.Button(top, text="⟳  Actualizar", font=FONT_SMALL,
                  bg="#2A3045", fg=ACCENT, relief="flat", padx=8,
                  cursor="hand2", command=self._do_refresh_hex).pack(side="left", padx=8)

        # Texto visor
        self.hex_view = tk.Text(viewer_frame, font=("Courier New", 10),
                                 bg=BG_INPUT, fg=TEXT_MAIN,
                                 insertbackground=ACCENT, relief="flat",
                                 state="disabled", bd=8, wrap="none",
                                 selectbackground="#1A3A5C", selectforeground=ACCENT)
        sb_h = ttk.Scrollbar(viewer_frame, orient="vertical", command=self.hex_view.yview)
        self.hex_view.configure(yscrollcommand=sb_h.set)
        sb_h.pack(side="right", fill="y")
        self.hex_view.pack(fill="both", expand=True)

        # Tags de colores por segmento
        for _, _, name, color in MEMORY_MAP:
            self.hex_view.tag_configure(name, foreground=color)
        self.hex_view.tag_configure("addr",   foreground=TEXT_ADDR)
        self.hex_view.tag_configure("zero",   foreground=TEXT_DIM)
        self.hex_view.tag_configure("accent", foreground=ACCENT)

    # ─── LOG ──────────────────────────────────────
    def _build_log(self, parent):
        tk.Label(parent, text="■  LOG DE OPERACIONES",
                 font=("Courier New", 9, "bold"), fg=TEXT_DIM,
                 bg=BG_DARK, anchor="w").pack(fill="x", pady=(6, 2))

        self.log = tk.Text(parent, font=("Courier New", 9),
                            bg=BG_MID, fg=TEXT_DIM, relief="flat",
                            height=4, bd=6, state="disabled", wrap="word")
        self.log.pack(fill="x")
        self.log.tag_configure("ok",  foreground=ACCENT)
        self.log.tag_configure("err", foreground=ACCENT3)
        self.log.tag_configure("info",foreground=ACCENT2)

    # ─── HELPERS UI ───────────────────────────────
    def _panel(self, parent, title):
        outer = tk.Frame(parent, bg=BORDER, pady=1)
        outer.pack(fill="x", pady=5)
        inner = tk.Frame(outer, bg=BG_PANEL, padx=10, pady=8)
        inner.pack(fill="x")
        tk.Label(inner, text=title, font=("Courier New", 10, "bold"),
                 fg=ACCENT2, bg=BG_PANEL, anchor="w").pack(fill="x", pady=(0, 6))
        sep = tk.Frame(inner, bg=BORDER, height=1)
        sep.pack(fill="x", pady=(0, 6))
        return inner

    def _log(self, msg, tag="info"):
        self.log.configure(state="normal")
        self.log.insert("end", f"  {msg}\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _update_seg_label(self, *_):
        try:
            addr = int(self.addr_var.get(), 16)
            name, color = get_segment(addr)
            self.seg_label.configure(text=f"  ↳ Segmento: {name}", fg=color)
        except ValueError:
            self.seg_label.configure(text="  ↳ Dirección inválida", fg=ACCENT3)

    def _update_data_placeholder(self):
        pass  # El formato se muestra en el tooltip del modo

    def _refresh_prot_label(self):
        if ram.code_protected:
            self.prot_label.configure(text="PROTEGIDA 🔒", fg=ACCENT3)
        else:
            self.prot_label.configure(text="ABIERTA 🔓", fg=ACCENT)

    def _protect_code(self):
        ram.protect_code()
        self._refresh_prot_label()
        self._log("Zona de código PROTEGIDA — escrituras rechazadas", "err")

    def _unprotect_code(self):
        ram.unprotect_code()
        self._refresh_prot_label()
        self._log("Zona de código DESPROTEGIDA — escrituras permitidas", "ok")

    def _jump_to(self, addr):
        self.addr_var.set(f"{addr:08X}")
        self.hex_base_var.set(f"{addr:08X}")
        self._do_refresh_hex()
        self._log(f"Saltando a 0x{addr:08X}", "info")

    # ─── LÓGICA: PARSEO DE DATOS ──────────────────
    def _parse_data(self):
        raw = self.data_text.get("1.0", "end").strip()
        mode = self.data_mode.get()

        if not raw:
            return None, "El campo de datos está vacío."

        if mode == "hex":
            tokens = raw.replace(",", " ").split()
            result = []
            for t in tokens:
                t = t.strip()
                if not t:
                    continue
                if not re.fullmatch(r"[0-9A-Fa-f]{1,2}", t):
                    return None, f"Token hex inválido: '{t}' (se esperan bytes como FF, 0A, etc.)"
                result.append(int(t, 16))
            return bytes(result), None

        elif mode == "bin":
            tokens = raw.replace(",", " ").split()
            result = []
            for t in tokens:
                t = t.strip()
                if not t:
                    continue
                if not re.fullmatch(r"[01]{1,8}", t):
                    return None, f"Token binario inválido: '{t}' (se esperan grupos de 1–8 bits)"
                result.append(int(t, 2))
            return bytes(result), None

        elif mode == "dec":
            tokens = raw.replace(",", " ").split()
            result = []
            for t in tokens:
                t = t.strip()
                if not t:
                    continue
                try:
                    val = int(t)
                    if not (0 <= val <= 255):
                        return None, f"Valor decimal fuera de rango: {val} (0–255)"
                    result.append(val)
                except ValueError:
                    return None, f"Token decimal inválido: '{t}'"
            return bytes(result), None

        return None, "Modo de datos desconocido."

    # ─── LÓGICA: PARSEO DE DIRECCIÓN ─────────────
    def _parse_addr(self, var):
        raw = var.get().strip().replace("0x", "").replace("0X", "")
        if not raw:
            return None, "La dirección está vacía."
        if not re.fullmatch(r"[0-9A-Fa-f]{1,8}", raw):
            return None, f"Dirección hex inválida: '{raw}'"
        val = int(raw, 16)
        if val >= RAM_SIZE:
            return None, f"Dirección 0x{val:08X} fuera del rango de RAM (máx 0x{RAM_SIZE-1:08X})"
        return val, None

    # ─── ACCIONES ─────────────────────────────────
    def _do_write(self):
        addr, err = self._parse_addr(self.addr_var)
        if err:
            self._log(f"ERROR dirección: {err}", "err")
            messagebox.showerror("Error de dirección", err)
            return

        data, err = self._parse_data()
        if err:
            self._log(f"ERROR datos: {err}", "err")
            messagebox.showerror("Error de datos", err)
            return

        ok, msg = write_ram(addr, data)
        if ok:
            seg_name, _ = get_segment(addr)
            hex_str = " ".join(f"{b:02X}" for b in data)
            self._log(f"[WRITE] 0x{addr:08X}  [{seg_name}]  ← {hex_str}", "ok")
            # refrescar visor si la dirección coincide
            self.hex_base_var.set(f"{addr:08X}")
            self._refresh_hex_view(addr, 8)
        else:
            self._log(f"ERROR escritura: {msg}", "err")
            messagebox.showerror("Error de escritura", msg)

    def _do_read(self):
        addr, err = self._parse_addr(self.read_addr_var)
        if err:
            self._log(f"ERROR dirección lectura: {err}", "err")
            messagebox.showerror("Error", err)
            return
        try:
            length = int(self.read_len_var.get())
            if length <= 0 or length > 4096:
                raise ValueError
        except ValueError:
            self._log("ERROR: número de bytes inválido (1–4096)", "err")
            messagebox.showerror("Error", "Ingrese un número de bytes entre 1 y 4096.")
            return

        data, err = read_ram(addr, length)
        if err != "OK":
            self._log(f"ERROR lectura: {err}", "err")
            return

        hex_str = " ".join(f"{b:02X}" for b in data)
        seg_name, _ = get_segment(addr)
        self._log(f"[READ]  0x{addr:08X}  [{seg_name}]  → {hex_str}", "info")
        self.hex_base_var.set(f"{addr:08X}")
        self._refresh_hex_view(addr, max(1, length // 16))

    def _do_refresh_hex(self):
        try:
            addr = int(self.hex_base_var.get().strip(), 16)
        except ValueError:
            self._log("ERROR: dirección base del visor inválida", "err")
            return
        try:
            rows = int(self.hex_rows_var.get())
            rows = max(1, min(rows, 256))
        except ValueError:
            rows = 16
        self._refresh_hex_view(addr, rows)

    # ─── RENDERIZADO VISOR HEX ────────────────────
    def _refresh_hex_view(self, base_addr, rows=16):
        self.hex_view.configure(state="normal")
        self.hex_view.delete("1.0", "end")

        # Encabezado de columnas
        header = "  Dirección   " + "  ".join(f"{i:02X}" for i in range(16))
        header += "   │  ASCII\n"
        header += "  " + "─" * (len(header) - 2) + "\n"
        self.hex_view.insert("end", header, "addr")

        for row in range(rows):
            addr = base_addr + row * 16
            if addr >= RAM_SIZE:
                break

            seg_name, _ = get_segment(addr)
            chunk_size  = min(16, RAM_SIZE - addr)
            line_data   = ram.read(addr, chunk_size)

            # Dirección
            self.hex_view.insert("end", f"  0x{addr:08X}  ", "addr")

            # Bytes hex
            for i, b in enumerate(line_data):
                tag = "zero" if b == 0 else seg_name
                self.hex_view.insert("end", f"{b:02X} ", tag)

            # Relleno si la línea es corta
            if len(line_data) < 16:
                self.hex_view.insert("end", "   " * (16 - len(line_data)))

            # ASCII
            self.hex_view.insert("end", "  │  ")
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "·" for b in line_data)
            self.hex_view.insert("end", ascii_str + "\n", seg_name)

        self.hex_view.configure(state="disabled")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = CacaoRAMEditor()
    app.mainloop()