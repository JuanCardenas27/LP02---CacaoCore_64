"""
CACAO_Core-64 — Consola de Sistema
===================================
Componente de consola embebible para el panel de control.
Importar desde cacao_gui.py y adjuntar como self.console

Uso:
    from cacao_console import CacaoConsole
    self.console = CacaoConsole(parent_frame)
    self.console.frame.pack(fill="both", expand=True)

    # Metodos de escritura:
    self.console.write("Texto normal")
    self.console.write_info("Mensaje informativo")
    self.console.write_ok("Operacion exitosa")
    self.console.write_warn("Advertencia")
    self.console.write_error("Error critico")
    self.console.write_hex("Dato en hex", value=0xDEADBEEF)
    self.console.write_separator()
    self.console.clear()
"""

import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from gui.styles_console import *

# ── Niveles de mensaje ────────────────────────────────────────────────────
LEVELS = {
    "plain":  {"prefix": "  »  ", "color": TEXT_MAIN,  "bg": None},
    "info":   {"prefix": " [i] ", "color": ACCENT2,    "bg": None},
    "ok":     {"prefix": " [✓] ", "color": ACCENT,     "bg": None},
    "warn":   {"prefix": " [!] ", "color": ACCENT4,    "bg": None},
    "error":  {"prefix": " [✗] ", "color": ACCENT3,    "bg": "#1C0A0A"},
    "hex":    {"prefix": " [H] ", "color": ACCENT5,    "bg": None},
    "cmd":    {"prefix": " [>] ", "color": ACCENT4,    "bg": "#0D1008"},
    "sep":    {"prefix": "",      "color": TEXT_DIM,   "bg": None},
}

MAX_LINES = 2000   # limite de historial


# ══════════════════════════════════════════════════════════════════════════════
class CacaoConsole:
    """
    Consola de sistema embebible para CACAO_Core-64.

    Atributos publicos:
        frame       — tk.Frame raiz, empacarlo en el parent.
        text_widget — tk.Text subyacente (solo lectura recomendada).

    Metodos de escritura:
        write(msg, tag="plain")
        write_info(msg)
        write_ok(msg)
        write_warn(msg)
        write_error(msg)
        write_hex(label, value, bits=64)
        write_cmd(cmd_str)
        write_separator(char="─", length=60)
        clear()
        save_log()
    """

    def __init__(self, parent, show_timestamps: bool = True,
                 show_toolbar: bool = True):
        self._parent         = parent
        self._show_timestamps = show_timestamps
        self._line_count     = 0
        self._autoscroll     = tk.BooleanVar(value=True)

        self.frame = tk.Frame(parent, bg=BORDER, bd=1, relief="flat")
        self._build(show_toolbar)
        self._configure_tags()

        # Mensaje de bienvenida
        self.write_separator()
        self.write_info("CACAO_Core-64  ·  Consola de Sistema  v1.0")
        self.write_info("Sistema listo. Esperando instrucciones.")
        self.write_separator()

    # ─────────────────────────────────────────────────────────────────────
    #  CONSTRUCCION UI
    # ─────────────────────────────────────────────────────────────────────
    def _build(self, show_toolbar: bool):
        # Barra de titulo
        title_bar = tk.Frame(self.frame, bg=ACCENT3, pady=CONSOLE_TITLE_PADY)
        title_bar.pack(fill="x", side="top")

        tk.Label(title_bar, text=" ⬛  CONSOLA DE SISTEMA ",
                 font=FM_SM, fg=BG_DARK, bg=ACCENT3,
                 anchor="w").pack(side="left")

        # Indicador de lineas
        self._line_lbl = tk.Label(title_bar, text="0 líneas",
                                  font=FM_SM, fg=BG_DARK, bg=ACCENT3,
                                  anchor="e")
        self._line_lbl.pack(side="right", padx=CONSOLE_LINE_PADX)

        # Toolbar
        if show_toolbar:
            self._build_toolbar()

        # Area de texto + scrollbar
        text_frame = tk.Frame(self.frame, bg=BG_INPUT)
        text_frame.pack(fill="both", expand=True)

        vsb = tk.Scrollbar(text_frame, orient="vertical",
                           bg=BG_MID, troughcolor=BG_DARK,
                           activebackground=ACCENT2)
        vsb.pack(side="right", fill="y")

        self.text_widget = tk.Text(
            text_frame,
            font=FM,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT,
            selectbackground=ACCENT2,
            selectforeground=BG_DARK,
            relief="flat",
            bd=0,
            padx=CONSOLE_TEXT_PADX,
            pady=CONSOLE_TEXT_PADY,
            state="disabled",
            wrap="none",
            yscrollcommand=vsb.set,
            cursor="arrow",
        )
        self.text_widget.pack(side="left", fill="both", expand=True)
        vsb.configure(command=self.text_widget.yview)

        # Scrollbar horizontal
        hsb = tk.Scrollbar(self.frame, orient="horizontal",
                           bg=BG_MID, troughcolor=BG_DARK,
                           activebackground=ACCENT2)
        hsb.pack(side="bottom", fill="x")
        self.text_widget.configure(xscrollcommand=hsb.set)
        hsb.configure(command=self.text_widget.xview)

        # Input de comando (barra inferior)
        self._build_input_bar()

    def _build_toolbar(self):
        tb = tk.Frame(self.frame, bg=BG_MID, pady=CONSOLE_TOOLBAR_PADY)
        tb.pack(fill="x", side="top")

        # Autoscroll toggle
        asck = tk.Checkbutton(
            tb, text="Auto-scroll", variable=self._autoscroll,
            font=FM_SM, fg=TEXT_DIM, bg=BG_MID,
            selectcolor=BG_MID, activebackground=BG_MID,
            activeforeground=ACCENT2,
            cursor="hand2",
        )
        asck.pack(side="left", padx=6)

        # Filtro de nivel
        tk.Label(tb, text="Filtro:", font=FM_SM,
                 fg=TEXT_DIM, bg=BG_MID).pack(side="left")
        self._filter_var = tk.StringVar(value="ALL")
        for lvl_name, color in [("ALL", TEXT_MAIN), ("INFO", ACCENT2),
                                 ("OK", ACCENT), ("WARN", ACCENT4),
                                 ("ERR", ACCENT3)]:
            rb = tk.Radiobutton(
                tb, text=lvl_name, variable=self._filter_var, value=lvl_name,
                font=FM_SM, fg=color, bg=BG_MID,
                selectcolor=color,
                activebackground=BG_MID,
                indicatoron=False, padx=5, pady=1,
                relief="flat", cursor="hand2",
                command=self._apply_filter,
            )
            rb.pack(side="left", padx=2)

        # Botones accion
        for lbl, color, cmd in [
            ("CLR", ACCENT3, self.clear),
            ("LOG", ACCENT4, self.save_log),
        ]:
            btn = tk.Button(
                tb, text=lbl, font=FM_BTN,
                bg=BG_MID, fg=color,
                activebackground=color, activeforeground=BG_DARK,
                relief="flat", bd=0, padx=8, pady=1,
                cursor="hand2", command=cmd,
            )
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=c, fg=BG_DARK))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=BG_MID, fg=c))
            btn.pack(side="right", padx=3)

        tk.Frame(self.frame, bg=BORDER, height=1).pack(fill="x")

    def _build_input_bar(self):
        """Barra de entrada de comandos manual."""
        bar = tk.Frame(self.frame, bg=BG_MID, pady=CONSOLE_INPUT_PADY)
        bar.pack(fill="x", side="bottom")

        tk.Label(bar, text=" >", font=FM_BTN,
                 fg=ACCENT4, bg=BG_MID).pack(side="left", padx=(6, 0))

        self._cmd_var = tk.StringVar()
        cmd_entry = tk.Entry(
            bar, textvariable=self._cmd_var,
            font=FM, bg=BG_INPUT, fg=ACCENT4,
            insertbackground=ACCENT4,
            relief="flat", bd=4,
            highlightthickness=1,
            highlightcolor=ACCENT4,
            highlightbackground=BORDER,
        )
        cmd_entry.pack(side="left", fill="x", expand=True, padx=4)
        cmd_entry.bind("<Return>", self._submit_cmd)
        cmd_entry.bind("<Up>",     self._history_prev)
        cmd_entry.bind("<Down>",   self._history_next)

        send_btn = tk.Button(
            bar, text="SEND", font=FM_BTN,
            bg=BG_MID, fg=ACCENT4,
            activebackground=ACCENT4, activeforeground=BG_DARK,
            relief="flat", bd=0, padx=10,
            cursor="hand2", command=self._submit_cmd,
        )
        send_btn.bind("<Enter>", lambda e: send_btn.config(bg=ACCENT4, fg=BG_DARK))
        send_btn.bind("<Leave>", lambda e: send_btn.config(bg=BG_MID,  fg=ACCENT4))
        send_btn.pack(side="right", padx=4)

        # Historial de comandos
        self._cmd_history = []
        self._cmd_hist_idx = -1

    # ─────────────────────────────────────────────────────────────────────
    #  TAGS DE COLORES
    # ─────────────────────────────────────────────────────────────────────
    def _configure_tags(self):
        tw = self.text_widget
        for tag, cfg in LEVELS.items():
            kw = {"foreground": cfg["color"]}
            if cfg["bg"]:
                kw["background"] = cfg["bg"]
            tw.tag_configure(tag, **kw)

        # Tag timestamp
        tw.tag_configure("ts",  foreground=TEXT_DIM)
        tw.tag_configure("sep", foreground=TEXT_DIM)
        tw.tag_configure("hex_val", foreground=ACCENT5)

    # ─────────────────────────────────────────────────────────────────────
    #  ESCRITURA INTERNA
    # ─────────────────────────────────────────────────────────────────────
    def _append(self, prefix: str, msg: str, tag: str,
                ts: str | None = None, extra_tag: str | None = None):
        """Inserta una linea en el widget de texto."""
        self._trim_if_needed()

        tw = self.text_widget
        tw.configure(state="normal")

        # Timestamp
        if ts and self._show_timestamps:
            tw.insert("end", ts + " ", "ts")

        # Prefijo
        if prefix:
            tw.insert("end", prefix, tag)

        # Mensaje
        if extra_tag:
            tw.insert("end", msg, extra_tag)
        else:
            tw.insert("end", msg, tag)

        tw.insert("end", "\n")
        tw.configure(state="disabled")

        self._line_count += 1
        self._line_lbl.config(text=f"{self._line_count} líneas")

        if self._autoscroll.get():
            tw.see("end")

    def _trim_if_needed(self):
        if self._line_count >= MAX_LINES:
            self.text_widget.configure(state="normal")
            self.text_widget.delete("1.0", f"{MAX_LINES // 4}.0")
            self.text_widget.configure(state="disabled")
            self._line_count -= MAX_LINES // 4

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    # ─────────────────────────────────────────────────────────────────────
    #  API PUBLICA — METODOS DE ESCRITURA
    # ─────────────────────────────────────────────────────────────────────
    def write(self, msg: str, tag: str = "plain"):
        """
        Escribe un mensaje con el tag indicado.
        Tags validos: 'plain', 'info', 'ok', 'warn', 'error', 'hex', 'cmd', 'sep'.
        """
        cfg = LEVELS.get(tag, LEVELS["plain"])
        self._append(cfg["prefix"], str(msg), tag, self._timestamp())

    def write_info(self, msg: str):
        """Mensaje informativo (azul cian)."""
        self.write(msg, "info")

    def write_ok(self, msg: str):
        """Operacion exitosa (verde)."""
        self.write(msg, "ok")

    def write_warn(self, msg: str):
        """Advertencia (amarillo)."""
        self.write(msg, "warn")

    def write_error(self, msg: str):
        """Error critico (rojo, fondo oscuro)."""
        self.write(msg, "error")

    def write_hex(self, label: str, value: int, bits: int = 64):
        """
        Escribe un par etiqueta: valor hexadecimal.
        Ej: write_hex("PC", 0x1000)  ->  [H] PC: 0x0000000000001000
        """
        mask = (1 << bits) - 1
        val  = int(value) & mask
        hex_str = f"0x{val:0{bits//4}X}"
        cfg = LEVELS["hex"]
        ts  = self._timestamp()
        self._trim_if_needed()

        tw = self.text_widget
        tw.configure(state="normal")
        if self._show_timestamps:
            tw.insert("end", ts + " ", "ts")
        tw.insert("end", cfg["prefix"], "hex")
        tw.insert("end", f"{label}: ", "hex")
        tw.insert("end", hex_str + "\n", "hex_val")
        tw.configure(state="disabled")

        self._line_count += 1
        self._line_lbl.config(text=f"{self._line_count} líneas")
        if self._autoscroll.get():
            tw.see("end")

    def write_cmd(self, cmd_str: str):
        """Registra un comando emitido (amarillo, fondo verde oscuro)."""
        self.write(cmd_str, "cmd")

    def write_separator(self, char: str = "─", length: int = 64):
        """Inserta una linea separadora decorativa."""
        line = char * length
        cfg  = LEVELS["sep"]
        self._append("", line, "sep", ts=None)

    def clear(self):
        """Limpia toda la consola."""
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.configure(state="disabled")
        self._line_count = 0
        self._line_lbl.config(text="0 líneas")
        self.write_info("Consola limpiada.")

    def save_log(self):
        """Guarda el contenido de la consola en un archivo .txt."""
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Guardar log de consola",
            initialfile=f"cacao_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if not path:
            return
        content = self.text_widget.get("1.0", "end")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.write_ok(f"Log guardado en: {path}")
        except Exception as e:
            self.write_error(f"No se pudo guardar el log: {e}")

    # ─────────────────────────────────────────────────────────────────────
    #  FILTRO (muestra/oculta segun nivel)
    # ─────────────────────────────────────────────────────────────────────
    def _apply_filter(self):
        """
        Aplica visibilidad a los tags segun el filtro seleccionado.
        En modo ALL todos los tags son visibles.
        """
        selected = self._filter_var.get()
        level_map = {
            "ALL":  None,
            "INFO": "info",
            "OK":   "ok",
            "WARN": "warn",
            "ERR":  "error",
        }
        chosen = level_map.get(selected)
        tw = self.text_widget

        for tag in LEVELS:
            if chosen is None or tag == chosen or tag in ("sep", "plain"):
                tw.tag_configure(tag, elide=False)
                tw.tag_configure("ts", elide=False)
            else:
                tw.tag_configure(tag, elide=True)

    # ─────────────────────────────────────────────────────────────────────
    #  INPUT DE COMANDOS
    # ─────────────────────────────────────────────────────────────────────
    def _submit_cmd(self, event=None):
        cmd = self._cmd_var.get().strip()
        if not cmd:
            return
        self._cmd_var.set("")

        # Historial
        if not self._cmd_history or self._cmd_history[-1] != cmd:
            self._cmd_history.append(cmd)
        self._cmd_hist_idx = -1

        self.write_cmd(cmd)

        # Comandos internos basicos
        lower = cmd.lower()
        if lower in ("clear", "cls", "limpiar"):
            self.clear()
        elif lower in ("help", "ayuda", "?"):
            self._print_help()
        else:
            self.write_warn(f"Comando desconocido: '{cmd}'  (escribe 'help' para ayuda)")

    def _history_prev(self, event=None):
        if not self._cmd_history:
            return
        self._cmd_hist_idx = max(0, self._cmd_hist_idx - 1) \
            if self._cmd_hist_idx != -1 \
            else len(self._cmd_history) - 1
        self._cmd_var.set(self._cmd_history[self._cmd_hist_idx])

    def _history_next(self, event=None):
        if self._cmd_hist_idx == -1 or not self._cmd_history:
            return
        self._cmd_hist_idx += 1
        if self._cmd_hist_idx >= len(self._cmd_history):
            self._cmd_hist_idx = -1
            self._cmd_var.set("")
        else:
            self._cmd_var.set(self._cmd_history[self._cmd_hist_idx])

    def _print_help(self):
        self.write_separator()
        self.write_info("Comandos disponibles:")
        self.write("  clear / cls / limpiar  — Limpiar consola",    "plain")
        self.write("  help  / ayuda  / ?     — Mostrar esta ayuda",  "plain")
        self.write_separator()
