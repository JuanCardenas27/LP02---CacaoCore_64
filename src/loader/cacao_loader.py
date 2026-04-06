"""
CACAO_Core-64 — Lógica de carga de archivos ORIGINAL (extraída de cacao_ram_editor.py)
========================================================================================
Este archivo conserva la implementación antigua de carga de archivos .txt a RAM,
tal como existía en cacao_ram_editor.py antes de ser reemplazada por cacao_loader.py.

Funciones/métodos extraídos tal cual, sin modificaciones.
Solo se añadieron los imports mínimos para que el módulo sea importable de forma aislada.
"""

import re
from tkinter import messagebox
from memoria.ram import ram


class Loader:

    def load_to_ram(self, lines, base_addr, mode):

        current_addr   = base_addr
        bytes_per_line = 8     # siempre 8 bytes por línea (rellena con 0x00)
        step           = 8     # avance fijo de 8 bytes aunque la línea tenga menos

        for idx, line in enumerate(lines):

            line = line.strip()
            if not line:
                current_addr += step   # líneas vacías avanzan igualmente
                continue

            tokens = line.replace(",", " ").split()
            if len(tokens) == 1 and len(tokens[0]) == 16:
                tokens = [tokens[0][i]+tokens[0][i+1] for i in range(16) if i % 2 == 0]
                print(tokens)
            parsed_bytes = []

            for t in tokens:
                t = t.strip()
                if not t:
                    continue

                if mode == "hex":
                    if not re.fullmatch(r"[0-9A-Fa-f]{1,2}", t):
                        messagebox.showerror(
                            "Error de formato",
                            f"Línea {idx+1}: token hex inválido '{t}'"
                        )
                        return
                    parsed_bytes.append(int(t, 16))

                elif mode == "bin":
                    if not re.fullmatch(r"[01]{1,8}", t):
                        messagebox.showerror(
                            "Error de formato",
                            f"Línea {idx+1}: token binario inválido '{t}'"
                        )
                        return
                    parsed_bytes.append(int(t, 2))

                elif mode == "dec":
                    try:
                        val = int(t)
                        if not (0 <= val <= 255):
                            raise ValueError
                        parsed_bytes.append(val)
                    except ValueError:
                        messagebox.showerror(
                            "Error de formato",
                            f"Línea {idx+1}: token decimal inválido '{t}'"
                        )
                        return

                else: 
                    messagebox.showerror(
                        "Error",
                        f"Modo de lectura inválido."
                    )
                    return

            if len(parsed_bytes) > bytes_per_line:
                messagebox.showerror(
                    "Error",
                    f"Línea {idx+1} excede {bytes_per_line} bytes."
                )
                return

            # Rellena con ceros hasta completar bytes_per_line
            while len(parsed_bytes) < bytes_per_line:
                parsed_bytes.append(0)

            ram.write(current_addr, bytes(parsed_bytes))
            current_addr += step


    def read_and_load(self, path, base_addr, mode):
        with open(path, "r") as f:
            lines = f.readlines()
        self.load_to_ram(lines, base_addr, mode)
        return lines


# Instancia global del cargador
loader = Loader()