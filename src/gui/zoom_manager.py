import tkinter as tk
from tkinter import font
from gui.theme_manager import recolor_widget_tree


class ZoomSetting:
    def __init__(self, on_change, min_zoom=0.5, max_zoom=1.9):
        self._zoom = 1.0
        self._on_change = on_change
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom

    def get_zoomed(self, font_tuple):
        values = list(font_tuple)
        new_size = int(round(values[1] * self._zoom, 0))
        if self._zoom < 1.0:
            values[1] = min(new_size, values[1] - 1)
        elif self._zoom > 1.0:
            values[1] = max(new_size, values[1] + 1)
        return tuple(values)

    def set_zoom(self, zoom):
        zoom = round(zoom, 1)
        self._zoom = max(self._min_zoom, min(self._max_zoom, zoom))
        self._on_change()

    def zoom_in(self, factor=0.1):
        self.set_zoom(self._zoom + float(factor))

    def zoom_out(self, factor=0.1):
        self.set_zoom(self._zoom - float(factor))

    def reset_zoom(self):
        self.set_zoom(1.0)

    def get_current_zoom(self):
        return self._zoom


class ZoomManager:
    """Gestor de zoom de fuente y layout reusable para interfaces tkinter."""

    def __init__(
        self,
        app,
        *,
        font_base,
        font_lg,
        font_xl,
        font_title,
        font_subtitle,
        font_sm,
        font_btn,
        font_label,
        bg_panel,
        bg_mid,
        bg_dark,
        text_main,
        accent,
        accent2,
        accent4,
        min_layout_zoom=0.1,
        scale_widget_size=True,
        on_palette_change=None,
        initial_palette="current",
    ):
        self.app = app

        # Estilos base para el popup y actualizaciones puntuales
        self.font_base = font_base
        self.font_lg = font_lg
        self.font_xl = font_xl
        self.font_title = font_title
        self.font_subtitle = font_subtitle
        self.font_sm = font_sm
        self.font_btn = font_btn
        self.font_label = font_label

        self.bg_panel = bg_panel
        self.bg_mid = bg_mid
        self.bg_dark = bg_dark
        self.text_main = text_main
        self.accent = accent
        self.accent2 = accent2
        self.accent4 = accent4
        self._scale_widget_size = bool(scale_widget_size)
        self._on_palette_change = on_palette_change
        self._palette_name = initial_palette

        # Widgets enlazados desde la GUI anfitriona
        self._hdr_title = None
        self._hdr_subtitle = None
        self._hdr_info = None
        self._settings_btn = None
        self._status_label = None
        self._reg_labels = {}
        self._flag_widgets = {}
        self._format_rbs = []

        # Estado popup
        self._settings_popup = None
        self._font_zoom_label = None
        self._layout_zoom_label = None
        self._palette_buttons = {}

        # Estado de captura para zoom no acumulativo
        self._original_fonts = {}
        self._original_widget_layout = {}
        self._original_pack_layout = {}
        self._original_grid_layout = {}

        self.zoom_setting = ZoomSetting(
            on_change=lambda: self.apply_zoom("font"))
        self.layout_zoom_setting = ZoomSetting(
            on_change=lambda: self.apply_zoom("layout"),
            min_zoom=min_layout_zoom)

    def attach_widgets(
        self,
        *,
        header_title,
        header_subtitle,
        header_info,
        settings_button,
        status_label,
        reg_labels,
        flag_widgets,
        format_rbs,
    ):
        self._hdr_title = header_title
        self._hdr_subtitle = header_subtitle
        self._hdr_info = header_info
        self._settings_btn = settings_button
        self._status_label = status_label
        self._reg_labels = reg_labels
        self._flag_widgets = flag_widgets
        self._format_rbs = format_rbs

    def initialize(self):
        self._setup_shortcuts()
        self.capture_original_values()

    def _zoom_in_font(self, factor):
        self.zoom_setting.zoom_in(factor)
        if self.zoom_setting.get_current_zoom() > 1.0:
            self.layout_zoom_setting.zoom_out(factor)
    
    def _zoom_out_font(self, factor):
        self.zoom_setting.zoom_out(factor)
        if self.zoom_setting.get_current_zoom() >= 1.0:
            self.layout_zoom_setting.zoom_in(factor)
    
    def _zoom_reset_all(self):
        self.zoom_setting.reset_zoom()
        self.layout_zoom_setting.reset_zoom()

    def _setup_shortcuts(self):
        self.app.bind("<Control-plus>", lambda e: self._zoom_in_font(0.1))
        self.app.bind("<Control-minus>", lambda e: self._zoom_out_font(0.1))
        self.app.bind("<Control-0>", lambda e: self._zoom_reset_all())

    def toggle_settings_popup(self):
        if self._settings_popup is not None and self._settings_popup.winfo_exists():
            self.close_settings_popup()
            return
        self.open_settings_popup()

    def open_settings_popup(self):
        popup = tk.Toplevel(self.app)
        self._settings_popup = popup
        popup.title("Configuracion")
        popup.configure(bg=self.bg_panel)
        popup.resizable(False, False)
        popup.transient(self.app)
        popup.wm_attributes("-topmost", True)
        popup.protocol("WM_DELETE_WINDOW", self.close_settings_popup)

        popup.update_idletasks()
        btn_x = self._settings_btn.winfo_rootx()
        btn_y = self._settings_btn.winfo_rooty() + self._settings_btn.winfo_height() + 6
        popup.geometry(f"360x235+{btn_x}+{btn_y}")

        root = tk.Frame(popup, bg=self.bg_panel, padx=12, pady=10)
        root.pack(fill="both", expand=True)

        tk.Label(
            root,
            text="Ajustes rapidos",
            font=self.font_lg,
            fg=self.accent2,
            bg=self.bg_panel,
        ).pack(anchor="w", pady=(0, 8))

        font_row = tk.Frame(root, bg=self.bg_panel)
        font_row.pack(fill="x", pady=(0, 6))
        tk.Label(
            font_row,
            text="Texto",
            font=self.font_label,
            fg=self.text_main,
            bg=self.bg_panel,
            width=10,
            anchor="w",
        ).pack(side="left")

        tk.Button(
            font_row,
            text="-",
            font=self.font_btn,
            bg=self.bg_mid,
            fg=self.accent4,
            activebackground=self.accent4,
            activeforeground=self.bg_dark,
            relief="flat",
            bd=0,
            width=3,
            command=lambda: self._zoom_out_font(0.1),
        ).pack(side="left", padx=(4, 2))

        self._font_zoom_label = tk.Label(
            font_row,
            text="100%",
            font=self.font_label,
            fg=self.accent4,
            bg=self.bg_panel,
            width=6,
        )
        self._font_zoom_label.pack(side="left", padx=4)

        tk.Button(
            font_row,
            text="+",
            font=self.font_btn,
            bg=self.bg_mid,
            fg=self.accent4,
            activebackground=self.accent4,
            activeforeground=self.bg_dark,
            relief="flat",
            bd=0,
            width=3,
            command=lambda: self._zoom_in_font(0.1),
        ).pack(side="left", padx=2)

        tk.Button(
            font_row,
            text="Reset",
            font=self.font_sm,
            bg=self.bg_mid,
            fg=self.accent,
            activebackground=self.accent,
            activeforeground=self.bg_dark,
            relief="flat",
            bd=0,
            command=self.zoom_setting.reset_zoom,
        ).pack(side="right")

        layout_row = tk.Frame(root, bg=self.bg_panel)
        layout_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            layout_row,
            text="Layout",
            font=self.font_label,
            fg=self.text_main,
            bg=self.bg_panel,
            width=10,
            anchor="w",
        ).pack(side="left")

        tk.Button(
            layout_row,
            text="-",
            font=self.font_btn,
            bg=self.bg_mid,
            fg=self.accent4,
            activebackground=self.accent4,
            activeforeground=self.bg_dark,
            relief="flat",
            bd=0,
            width=3,
            command=lambda: self.layout_zoom_setting.zoom_out(0.1),
        ).pack(side="left", padx=(4, 2))

        self._layout_zoom_label = tk.Label(
            layout_row,
            text="100%",
            font=self.font_label,
            fg=self.accent4,
            bg=self.bg_panel,
            width=6,
        )
        self._layout_zoom_label.pack(side="left", padx=4)

        tk.Button(
            layout_row,
            text="+",
            font=self.font_btn,
            bg=self.bg_mid,
            fg=self.accent4,
            activebackground=self.accent4,
            activeforeground=self.bg_dark,
            relief="flat",
            bd=0,
            width=3,
            command=lambda: self.layout_zoom_setting.zoom_in(0.1),
        ).pack(side="left", padx=2)

        tk.Button(
            layout_row,
            text="Reset",
            font=self.font_sm,
            bg=self.bg_mid,
            fg=self.accent,
            activebackground=self.accent,
            activeforeground=self.bg_dark,
            relief="flat",
            bd=0,
            command=self.layout_zoom_setting.reset_zoom,
        ).pack(side="right")

        palette_row = tk.Frame(root, bg=self.bg_panel)
        palette_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            palette_row,
            text="Tema",
            font=self.font_label,
            fg=self.text_main,
            bg=self.bg_panel,
            width=10,
            anchor="w",
        ).pack(side="left")

        self._palette_buttons = {}
        self._palette_buttons["current"] = tk.Button(
            palette_row,
            text="Cacao Tropical",
            font=self.font_sm,
            bg=self.bg_mid,
            fg=self.accent4,
            activebackground=self.accent4,
            activeforeground=self.bg_dark,
            relief="flat",
            bd=0,
            padx=10,
            pady=2,
            command=lambda: self.set_palette("current"),
        )
        self._palette_buttons["current"].pack(side="left", padx=(4, 4))

        self._palette_buttons["legacy"] = tk.Button(
            palette_row,
            text="Neón",
            font=self.font_sm,
            bg=self.bg_mid,
            fg=self.accent4,
            activebackground=self.accent4,
            activeforeground=self.bg_dark,
            relief="flat",
            bd=0,
            padx=10,
            pady=2,
            command=lambda: self.set_palette("legacy"),
        )
        self._palette_buttons["legacy"].pack(side="left", padx=4)

        tk.Button(
            root,
            text="Cerrar",
            font=self.font_sm,
            bg=self.bg_mid,
            fg=self.accent2,
            activebackground=self.accent2,
            activeforeground=self.bg_dark,
            relief="flat",
            bd=0,
            command=self.close_settings_popup,
        ).pack(anchor="e")

        self._apply_palette_to_popup()
        self.apply_zoom()

    def close_settings_popup(self):
        if self._settings_popup is not None and self._settings_popup.winfo_exists():
            self._settings_popup.destroy()
        self._settings_popup = None
        self._font_zoom_label = None
        self._layout_zoom_label = None
        self._palette_buttons = {}

    def set_palette(self, palette_name):
        if palette_name not in ("current", "legacy"):
            return
        self._palette_name = palette_name
        if self._on_palette_change is not None:
            self._on_palette_change(palette_name)
        self._apply_palette_to_popup()

    def _apply_palette_to_popup(self):
        if self._settings_popup is None or not self._settings_popup.winfo_exists():
            return
        recolor_widget_tree(self._settings_popup, self._palette_name)
        for name, btn in self._palette_buttons.items():
            try:
                if name == self._palette_name:
                    btn.configure(relief="sunken", bd=1)
                else:
                    btn.configure(relief="flat", bd=0)
            except Exception:
                pass

    def _is_in_settings_popup(self, widget):
        if self._settings_popup is None or not self._settings_popup.winfo_exists():
            return False
        return widget.winfo_toplevel() == self._settings_popup

    def _parse_layout_value(self, value):
        if isinstance(value, (int, float)):
            return int(value)

        if isinstance(value, str):
            parts = value.strip().split()
            if len(parts) == 1:
                token = parts[0]
                if token.isdigit():
                    return int(token)
                if token.startswith("-") and token[1:].isdigit():
                    return -int(token[1:])
            elif len(parts) == 2:
                a, b = parts
                a_ok = a.isdigit() or (a.startswith("-") and a[1:].isdigit())
                b_ok = b.isdigit() or (b.startswith("-") and b[1:].isdigit())
                if a_ok and b_ok:
                    return (int(a), int(b))
        return None

    def _scale_layout_value(self, value, zoom):
        if isinstance(value, tuple):
            return tuple(max(0, int(round(v * zoom))) for v in value)
        return max(0, int(round(value * zoom)))

    def _to_tk_layout_value(self, value):
        if isinstance(value, tuple):
            return f"{value[0]} {value[1]}"
        return value

    def _capture_widget_layout_options(self, parent):
        if self._is_in_settings_popup(parent):
            return

        widget_id = id(parent)

        option_keys = [
            "padx",
            "pady",
            "ipadx",
            "ipady",
            "bd",
            "borderwidth",
            "highlightthickness",
            "insertwidth",
            "wraplength",
        ]
        if self._scale_widget_size:
            option_keys.extend(["width", "height"])

        widget_options = {}
        widget_available_keys = set(parent.keys())
        for key in option_keys:
            if key in widget_available_keys:
                parsed = self._parse_layout_value(parent.cget(key))
                if parsed is not None:
                    widget_options[key] = parsed

        if widget_options and widget_id not in self._original_widget_layout:
            self._original_widget_layout[widget_id] = widget_options

        manager = parent.winfo_manager()
        manager_keys = ("padx", "pady", "ipadx", "ipady")

        if manager == "pack":
            pack_info = parent.pack_info()
            pack_options = {}
            for key in manager_keys:
                if key in pack_info:
                    parsed = self._parse_layout_value(pack_info[key])
                    if parsed is not None:
                        pack_options[key] = parsed
            if pack_options and widget_id not in self._original_pack_layout:
                self._original_pack_layout[widget_id] = pack_options

        elif manager == "grid":
            grid_info = parent.grid_info()
            grid_options = {}
            for key in manager_keys:
                if key in grid_info:
                    parsed = self._parse_layout_value(grid_info[key])
                    if parsed is not None:
                        grid_options[key] = parsed
            if grid_options and widget_id not in self._original_grid_layout:
                self._original_grid_layout[widget_id] = grid_options

    def capture_original_values(self):
        self._capture_widget_fonts(self.app)

    def _capture_widget_fonts(self, parent):
        if self._is_in_settings_popup(parent):
            return

        widget_id = id(parent)
        self._capture_widget_layout_options(parent)

        if isinstance(parent, (tk.Label, tk.Button, tk.Entry, tk.Text, tk.Radiobutton)):
            current_font = parent.cget("font")
            if current_font:
                font_obj = font.Font(font=current_font)
                family = font_obj.actual("family")
                size = font_obj.actual("size")
                weight = font_obj.actual("weight")
                font_tuple = (family, size, "bold") if weight == "bold" else (family, size)
                if widget_id not in self._original_fonts:
                    self._original_fonts[widget_id] = font_tuple

        for child in parent.winfo_children():
            self._capture_widget_fonts(child)

    def apply_zoom(self, apply_type="both"):
        if apply_type in ("font", "both"):
            font_zoom = self.zoom_setting.get_current_zoom()
            if self._font_zoom_label is not None:
                self._font_zoom_label.config(text=f"{int(font_zoom * 100)}%")

            if self._hdr_title is not None:
                self._hdr_title.config(font=self.zoom_setting.get_zoomed(self.font_title))
            if self._hdr_subtitle is not None:
                self._hdr_subtitle.config(font=self.zoom_setting.get_zoomed(self.font_subtitle))
            if self._hdr_info is not None:
                self._hdr_info.config(font=self.zoom_setting.get_zoomed(self.font_sm))
            if self._settings_btn is not None:
                self._settings_btn.config(font=self.zoom_setting.get_zoomed(self.font_btn))

            for name, lbl in self._reg_labels.items():
                if name in ("pc", "ir"):
                    lbl.config(font=self.zoom_setting.get_zoomed(self.font_xl))
                elif name in ("sp", "lr", "acc"):
                    lbl.config(font=self.zoom_setting.get_zoomed(self.font_lg))
                else:
                    lbl.config(font=self.zoom_setting.get_zoomed(self.font_base))

            for rb in self._format_rbs:
                rb.config(font=self.zoom_setting.get_zoomed(self.font_btn))

            for _, (ind, _) in self._flag_widgets.items():
                ind.config(font=self.zoom_setting.get_zoomed((self.font_base[0], 28, "bold")))

            if self._status_label is not None:
                self._status_label.config(font=self.zoom_setting.get_zoomed(self.font_sm))

            self._apply_font_zoom_recursive(self.app)

        if apply_type in ("layout", "both"):
            layout_zoom = self.layout_zoom_setting.get_current_zoom()
            if self._layout_zoom_label is not None:
                self._layout_zoom_label.config(text=f"{int(layout_zoom * 100)}%")
            self._apply_layout_zoom_recursive(self.app, layout_zoom)

    def _apply_font_zoom_recursive(self, parent):
        if self._is_in_settings_popup(parent):
            return

        widget_id = id(parent)
        if isinstance(parent, (tk.Label, tk.Button, tk.Entry, tk.Text, tk.Radiobutton)):
            if widget_id in self._original_fonts:
                parent.config(font=self.zoom_setting.get_zoomed(self._original_fonts[widget_id]))

        for child in parent.winfo_children():
            self._apply_font_zoom_recursive(child)

    def _apply_layout_zoom_recursive(self, parent, layout_zoom):
        if self._is_in_settings_popup(parent):
            return

        widget_id = id(parent)

        if widget_id in self._original_widget_layout:
            original_widget_options = self._original_widget_layout[widget_id]
            updates = {}
            current_widget_keys = set(parent.keys())
            for key, original_value in original_widget_options.items():
                if key not in current_widget_keys:
                    continue
                scaled = self._scale_layout_value(original_value, layout_zoom)
                if key in ("width", "height") and isinstance(original_value, int) and original_value > 0:
                    scaled = max(1, scaled)
                updates[key] = self._to_tk_layout_value(scaled)
            if updates:
                parent.config(**updates)

        manager = parent.winfo_manager()
        if manager == "pack" and widget_id in self._original_pack_layout:
            pack_updates = {}
            for key, original_value in self._original_pack_layout[widget_id].items():
                scaled = self._scale_layout_value(original_value, layout_zoom)
                pack_updates[key] = self._to_tk_layout_value(scaled)
            if pack_updates:
                parent.pack_configure(**pack_updates)

        elif manager == "grid" and widget_id in self._original_grid_layout:
            grid_updates = {}
            for key, original_value in self._original_grid_layout[widget_id].items():
                scaled = self._scale_layout_value(original_value, layout_zoom)
                grid_updates[key] = self._to_tk_layout_value(scaled)
            if grid_updates:
                parent.grid_configure(**grid_updates)

        for child in parent.winfo_children():
            self._apply_layout_zoom_recursive(child, layout_zoom)
