"""
CACAO_Core-64 — Editor de Disco Persistente
Permite listar, leer, guardar y borrar archivos del disco simulado.
"""

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Permitir import desde el PC solo en modo desarrollo (setear CACAO_DEV_MODE=1)
DEV_MODE = os.environ.get('CACAO_DEV_MODE', '0') == '1'

import gui.styles_cacao as styles_cacao_module
from gui.styles_cacao import *
from gui.theme_manager import apply_palette_namespace, recolor_widget_tree
from gui.zoom_manager import ZoomManager


class CacaoDiskEditor:
    def __init__(self):
        super().__init__()

    # ─────────────────────────────────────────────────────────────────────
    #  UI
    # ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_DARK, pady=8)
        hdr.pack(fill="x", padx=16)

        self._hdr_title = tk.Label(
            hdr,
            text="▓▓  CACAO_Core-64",
            font=FM_TITLE,
            fg=ACCENT,
            bg=BG_DARK,
        )
        self._hdr_title.pack(side="left")

        self._hdr_subtitle = tk.Label(
            hdr,
            text="  DISK EDITOR",
            font=("Courier New", 13),
            fg=ACCENT2,
            bg=BG_DARK,
        )
        self._hdr_subtitle.pack(side="left", padx=8)

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

        size_mb = int(getattr(self.disk, "size_bytes", 0) / (1024 * 1024))
        block = getattr(self.disk, "block_size", 0)
        self._hdr_info = tk.Label(
            hdr,
            text=f"{size_mb} MB  ·  {block} B/block  │  simple_fs",
            font=FM_SM,
            fg=TEXT_DIM,
            bg=BG_DARK,
        )
        self._hdr_info.pack(side="left")

        sep = tk.Frame(self, bg=ACCENT, height=1)
        sep.pack(fill="x", padx=16)

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=8)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1, uniform="disk_cols")
        body.grid_columnconfigure(1, weight=2, uniform="disk_cols")

        left = tk.Frame(body, bg=BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right = tk.Frame(body, bg=BG_DARK)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_file_list(left)
        self._build_editor(right)
        self._init_zoom_controls()

    def _build_file_list(self, parent):
        outer = tk.Frame(parent, bg=BORDER, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=BG_PANEL, padx=10, pady=8)
        inner.pack(fill="both", expand=True)

        tk.Label(
            inner,
            text="◈  ARCHIVOS EN DISCO",
            font=FM_BTN,
            fg=ACCENT2,
            bg=BG_PANEL,
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        search_row = tk.Frame(inner, bg=BG_PANEL)
        search_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            search_row,
            text="Buscar:",
            font=FM_SM,
            fg=TEXT_DIM,
            bg=BG_PANEL,
        ).pack(side="left")
        if not hasattr(self, "search_var"):
            self.search_var = tk.StringVar(value="")
        search_entry = tk.Entry(
            search_row,
            textvariable=self.search_var,
            font=FM,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT,
            relief="flat",
            bd=4,
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=6)
        search_entry.bind("<KeyRelease>", lambda _e: self._refresh_file_list())

        tk.Button(
            search_row,
            text="✕",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT4,
            relief="flat",
            cursor="hand2",
            command=self._clear_search,
        ).pack(side="left")

        self._apply_tree_style()

        columns = ("name", "size", "mtime")
        self.file_list = ttk.Treeview(
            inner,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=16,
            style="Disk.Treeview",
        )
        self.file_list.heading("name", text="Archivo")
        self.file_list.heading("size", text="Tam")
        self.file_list.heading("mtime", text="Modificado")
        self.file_list.column("name", width=220, anchor="w")
        self.file_list.column("size", width=80, anchor="e")
        self.file_list.column("mtime", width=140, anchor="center")
        self.file_list.pack(fill="both", expand=True)
        self.file_list.bind("<<TreeviewSelect>>", self._on_select)
        self.file_list.bind("<Double-1>", self._load_selected)

        btn_row = tk.Frame(inner, bg=BG_PANEL)
        btn_row.pack(fill="x", pady=(8, 0))

        tk.Button(
            btn_row,
            text="⟳  REFRESCAR",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT,
            relief="flat",
            cursor="hand2",
            command=self._refresh_file_list,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(
            btn_row,
            text="🗑  BORRAR",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT3,
            relief="flat",
            cursor="hand2",
            command=self._delete_selected,
        ).pack(side="left", fill="x", expand=True)

    def _build_editor(self, parent):
        outer = tk.Frame(parent, bg=BORDER, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=BG_PANEL, padx=10, pady=8)
        inner.pack(fill="both", expand=True)

        tk.Label(
            inner,
            text="◈  EDITOR",
            font=FM_BTN,
            fg=ACCENT,
            bg=BG_PANEL,
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        name_row = tk.Frame(inner, bg=BG_PANEL)
        name_row.pack(fill="x", pady=(0, 6))
        tk.Label(
            name_row,
            text="Nombre:",
            font=FM_SM,
            fg=TEXT_DIM,
            bg=BG_PANEL,
        ).pack(side="left")

        self.filename_entry = tk.Entry(
            name_row,
            textvariable=self.filename_var,
            font=FM,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT,
            relief="flat",
            bd=4,
        )
        self.filename_entry.pack(side="left", fill="x", expand=True, padx=6)

        btn_row = tk.Frame(inner, bg=BG_PANEL)
        btn_row.pack(fill="x", pady=(0, 6))

        tk.Button(
            btn_row,
            text="📂  CARGAR",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT2,
            relief="flat",
            cursor="hand2",
            command=self._load_selected,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(
            btn_row,
            text="⬇  IMPORTAR",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT4,
            relief="flat",
            cursor="hand2",
            command=self._import_external,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(
            btn_row,
            text="💾  GUARDAR",
            font=FM_BTN,
            bg=ACCENT,
            fg=BG_DARK,
            relief="flat",
            cursor="hand2",
            command=self._save_file,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(
            btn_row,
            text="✕  NUEVO",
            font=FM_BTN,
            bg=BG_MID,
            fg=ACCENT4,
            relief="flat",
            cursor="hand2",
            command=self._new_file,
        ).pack(side="left", fill="x", expand=True)

        self.text_editor = tk.Text(
            inner,
            font=FM,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT,
            relief="flat",
            wrap="none",
            bd=8,
        )
        self.text_editor.pack(fill="both", expand=True)

        self._status_var = tk.StringVar(value="Listo")
        tk.Label(
            inner,
            textvariable=self._status_var,
            font=FM_SM,
            fg=TEXT_DIM,
            bg=BG_PANEL,
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

    # ─────────────────────────────────────────────────────────────────────
    #  Actions
    # ─────────────────────────────────────────────────────────────────────
    def _refresh_file_list(self):
        for row in self.file_list.get_children():
            self.file_list.delete(row)

        query = ""
        if hasattr(self, "search_var"):
            query = self.search_var.get().strip().lower()

        for entry in self.fs.list_files():
            name = entry.get("name", "")
            if query and query not in name.lower():
                continue
            size = entry.get("size", 0)
            mtime = entry.get("mtime", 0)
            mtime_txt = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime)) if mtime else "-"
            size_txt = self._fmt_size(size)
            self.file_list.insert("", "end", values=(name, size_txt, mtime_txt))

        self._set_status("Lista actualizada")

    def _clear_search(self):
        if hasattr(self, "search_var"):
            self.search_var.set("")
        self._refresh_file_list()

    def _on_select(self, _event=None):
        selection = self.file_list.selection()
        if not selection:
            return
        values = self.file_list.item(selection[0], "values")
        if values:
            self.filename_var.set(values[0])

    def _load_selected(self, _event=None):
        name = self.filename_var.get().strip()
        if not name:
            self._set_status("Selecciona un archivo")
            return
        try:
            data = self.fs.read_file(name)
        except Exception as exc:
            messagebox.showerror("Disco", f"No se pudo leer '{name}':\n{exc}")
            return
        text = data.decode("utf-8", errors="replace")
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", text)
        self._set_status(f"Archivo cargado: {name}")

    def _import_external(self):
        if not DEV_MODE:
            messagebox.showinfo(
                "Disco",
                "Import desde el filesystem deshabilitado en modo de producción."
            )
            return

        path = filedialog.askopenfilename(
            parent=self,
            title="Importar archivo",
            filetypes=[("All files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception as exc:
            messagebox.showerror("Disco", f"No se pudo abrir:\n{exc}")
            return

        base = os.path.basename(path)
        name, ext = os.path.splitext(base)
        if ext.lower() in (".choco", ".cacao"):
            suggested = base
        else:
            suggested = f"{name}.choco"

        self.filename_var.set(suggested)
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", text)
        self._set_status("Archivo externo cargado. Guarda para persistir.")

    def _save_file(self):
        name = self.filename_var.get().strip()
        if not name:
            messagebox.showerror("Disco", "Ingresa un nombre de archivo")
            return
        if not (name.endswith(".choco") or name.endswith(".cacao")):
            proceed = messagebox.askyesno(
                "Disco",
                "Extension no estandar. Guardar de todas formas?",
            )
            if not proceed:
                return

        text = self.text_editor.get("1.0", "end")
        data = text.encode("utf-8")
        try:
            self.fs.write_file(name, data)
            self.fs.flush()
            self._refresh_file_list()
            self._set_status(f"Archivo guardado: {name}")
        except Exception as exc:
            messagebox.showerror("Disco", f"No se pudo guardar '{name}':\n{exc}")

    def _delete_selected(self):
        name = self.filename_var.get().strip()
        if not name:
            self._set_status("Selecciona un archivo")
            return
        proceed = messagebox.askyesno("Disco", f"Borrar '{name}'?")
        if not proceed:
            return
        try:
            self.fs.delete_file(name)
            self.fs.flush()
            self._refresh_file_list()
            self.text_editor.delete("1.0", "end")
            self.filename_var.set("")
            self._set_status(f"Archivo borrado: {name}")
        except Exception as exc:
            messagebox.showerror("Disco", f"No se pudo borrar '{name}':\n{exc}")

    def _new_file(self):
        self.text_editor.delete("1.0", "end")
        self.filename_var.set("")
        self._set_status("Nuevo archivo")

    def _set_status(self, msg: str):
        self._status_var.set(msg)

    def _fmt_size(self, size_bytes: int) -> str:
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

    # ─────────────────────────────────────────────────────────────────────
    #  Zoom/palette
    # ─────────────────────────────────────────────────────────────────────
    def _init_zoom_controls(self):
        if self._zoom_manager is not None:
            return

        self._zoom_manager = ZoomManager(
            self,
            font_base=FM,
            font_lg=FM_LG,
            font_xl=FM_XL,
            font_title=FM_TITLE,
            font_subtitle=("Courier New", 13),
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
        recolor_widget_tree(self, palette_name)
        self._apply_tree_style()
        if self._zoom_manager is not None:
            self._zoom_manager.apply_zoom("both")

    def _on_close(self):
        try:
            self.fs.flush()
        finally:
            self.destroy()

    def _apply_tree_style(self):
        style = ttk.Style(self)
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
            "Treeview",
            background=BG_MID,
            fieldbackground=BG_MID,
            foreground=TEXT_MAIN,
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
