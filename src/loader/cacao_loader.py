"""
CACAO_Core-64 — Cargador de Programas
======================================
Adaptador que mantiene compatibilidad con los archivos .txt antiguos
pero usa internamente el nuevo sistema de enlazador-cargador.

Funcionalidad:
  - Lee archivos .txt en formato hexadecimal
  - Convierte internamente a módulos objeto
  - Usa el nuevo cargador para cargar a memoria
  - Mantiene la misma API pública

Ejemplo:
  from loader.cacao_loader import loader
  loader.read_and_load('examples/Short_example.txt', 0x1000, 'hex')
"""

import re
from typing import List, Optional
from tkinter import messagebox
from memoria.ram import ram
from enlazador_cargador.gestor_enlazador_cargador import GestorEnlazadorCargador


class Loader:
    """
    Cargador compatible con la API antigua pero implementado con el nuevo sistema.
    
    Convierte archivos .txt a módulos objeto y los carga usando el nuevo
    gestor de enlazador-cargador.
    """

    def __init__(self):
        self.gestor = GestorEnlazadorCargador(verbose=False)

    def load_to_ram(self, lines: List[str], base_addr: int, mode: str) -> None:
        """
        Carga líneas de código a memoria RAM.
        
        Antes (versión antigua): Procesaba líneas directamente y escribía a RAM
        Ahora (versión nueva): Convierte a módulo objeto y usa el nuevo cargador
        
        Para direcciones de sistema (< 0x1000), carga directamente en RAM.
        Para direcciones de usuario (>= 0x1000), usa el nuevo cargador.
        
        Args:
            lines: Lista de líneas de código (hex, bin o dec)
            base_addr: Dirección base donde cargar
            mode: Formato ('hex', 'bin' o 'dec')
        
        Raises:
            messagebox.showerror: Si hay error en el formato
        """
        try:
            # Parsear líneas a bytes
            parsed_bytes = self._parse_lines(lines, mode)
            
            if not parsed_bytes:
                messagebox.showerror(
                    "Error",
                    "No se encontraron bytes válidos para cargar"
                )
                return

            # Casos especiales: direcciones de sistema (ROM/vectores)
            if base_addr < 0x1000:
                # Carga directa en RAM sin validación (es zona de sistema)
                self._cargar_directo_en_ram(parsed_bytes, base_addr)
            else:
                # Carga normal a través del nuevo gestor
                modulo_obj = self._crear_modulo_objeto(parsed_bytes, base_addr)
                exito = self.gestor.cargar_desde_contenido(
                    {'programa': modulo_obj},
                    direccion_base=base_addr,
                    cargar_en_memoria=True
                )
                
                if not exito:
                    messagebox.showerror(
                        "Error de carga",
                        f"Error al cargar: {self.gestor.obtener_ultimo_error()}"
                    )

        except Exception as e:
            messagebox.showerror(
                "Error inesperado",
                f"Error al cargar: {e}"
            )

    def _cargar_directo_en_ram(self, datos: bytearray, base_addr: int) -> None:
        """
        Carga datos directamente en RAM (para zonas de sistema).
        
        Args:
            datos: Bytes a cargar
            base_addr: Dirección base
        """
        for i, byte in enumerate(datos):
            ram.write(base_addr + i, byte)

    def _parse_lines(self, lines: List[str], mode: str) -> bytearray:
        """
        Parsea líneas de código en el formato especificado.
        
        Args:
            lines: Lista de líneas
            mode: 'hex', 'bin' o 'dec'
            
        Returns:
            bytearray con todos los bytes parseados
        """
        parsed_bytes = bytearray()
        bytes_per_line = 8

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                # Líneas vacías avanzan igualmente
                parsed_bytes.extend(bytes(bytes_per_line))
                continue

            # Separar por espacios o comas
            tokens = line.replace(",", " ").split()
            line_bytes = []

            for t in tokens:
                t = t.strip()
                if not t:
                    continue

                try:
                    if mode == "hex":
                        if not re.fullmatch(r"[0-9A-Fa-f]{1,2}", t):
                            messagebox.showerror(
                                "Error de formato",
                                f"Línea {idx+1}: token hex inválido '{t}'"
                            )
                            return bytearray()
                        line_bytes.append(int(t, 16))

                    elif mode == "bin":
                        if not re.fullmatch(r"[01]{1,8}", t):
                            messagebox.showerror(
                                "Error de formato",
                                f"Línea {idx+1}: token binario inválido '{t}'"
                            )
                            return bytearray()
                        line_bytes.append(int(t, 2))

                    elif mode == "dec":
                        val = int(t)
                        if not (0 <= val <= 255):
                            raise ValueError
                        line_bytes.append(val)

                    else:
                        messagebox.showerror(
                            "Error",
                            f"Modo de lectura inválido: {mode}"
                        )
                        return bytearray()

                except ValueError:
                    messagebox.showerror(
                        "Error de formato",
                        f"Línea {idx+1}: token '{t}' inválido en modo {mode}"
                    )
                    return bytearray()

            # Validar límite de bytes
            if len(line_bytes) > bytes_per_line:
                messagebox.showerror(
                    "Error",
                    f"Línea {idx+1} excede {bytes_per_line} bytes."
                )
                return bytearray()

            # Rellenar con ceros hasta completar bytes_per_line
            while len(line_bytes) < bytes_per_line:
                line_bytes.append(0)

            parsed_bytes.extend(line_bytes)

        return parsed_bytes

    def _crear_modulo_objeto(self, codigo_bytes: bytearray, base_addr: int) -> str:
        """
        Crea un módulo objeto en formato de texto a partir de bytes.
        
        Formato:
            [MODULE nombre]
            [CODE] ...hex bytes...
            [DATA]
            [SYMBOLS] simbolo:tipo:valor
            [EXTERNAL]
        
        Args:
            codigo_bytes: Bytes del programa
            base_addr: Dirección base
            
        Returns:
            String con el módulo objeto formateado
        """
        # Convertir bytes a hexadecimal separado por espacios
        code_hex = ' '.join(f'{byte:02X}' for byte in codigo_bytes)
        
        # Crear módulo objeto
        modulo = f"""[MODULE programa]
[CODE] {code_hex}
[DATA]
[SYMBOLS] inicio:code:0x{base_addr:X}
[EXTERNAL]
"""
        return modulo

    def read_and_load(self, path: str, base_addr: int, mode: str) -> Optional[List[str]]:
        """
        Lee un archivo y carga su contenido a memoria.
        
        API compatible con la versión anterior.
        
        Args:
            path: Ruta al archivo
            base_addr: Dirección base
            mode: Formato ('hex', 'bin', 'dec')
            
        Returns:
            Lista de líneas leídas, o None si hay error
        """
        try:
            with open(path, "r") as f:
                lines = f.readlines()
            
            # Cargar a memoria
            self.load_to_ram(lines, base_addr, mode)
            
            return lines

        except FileNotFoundError:
            messagebox.showerror(
                "Error",
                f"Archivo no encontrado: {path}"
            )
            return None
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al leer archivo: {e}"
            )
            return None


# Instancia global del cargador
loader = Loader()
