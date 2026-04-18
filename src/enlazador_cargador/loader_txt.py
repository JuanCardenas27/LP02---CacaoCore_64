"""
Cargador de Archivos de Texto (.txt)
====================================
Compatible con el formato antiguo (hex/bin/dec) pero usa internamente
el nuevo sistema de enlazador-cargador.

Funcionalidad:
  - Lee archivos .txt en formato hexadecimal, binario o decimal
  - Convierte internamente a módulos objeto
  - Usa el nuevo cargador para cargar a memoria
  - Mantiene la misma API pública

Ejemplo:
  from enlazador_cargador.loader_txt import loader_txt
  loader_txt.read_and_load('examples/Short_example.txt', 0x1000, 'hex')
"""

import re
from typing import List, Optional
from memoria.ram import ram
from .gestor_enlazador_cargador import GestorEnlazadorCargador


class LoaderTxt:
    """
    Cargador de archivos .txt compatible con la API antigua.
    
    Mantiene la interfaz original pero usa internamente el nuevo sistema
    de enlazador-cargador.
    """

    def __init__(self):
        self.gestor = GestorEnlazadorCargador(verbose=False)

    def load_to_ram(self, lines: List[str], base_addr: int, mode: str) -> None:
        """
        Carga líneas de código a memoria RAM.
        
        Para direcciones de sistema (< 0x1000), carga directamente en RAM.
        Para direcciones de usuario (>= 0x1000), usa el nuevo cargador.
        
        Args:
            lines: Lista de líneas de código (hex, bin o dec)
            base_addr: Dirección base donde cargar
            mode: Formato ('hex', 'bin' o 'dec')
        
        Raises:
            RuntimeError: Si hay error en el formato
        """
        try:
            # Parsear líneas a bytes
            parsed_bytes = self._parse_lines(lines, mode)
            
            if not parsed_bytes:
                raise RuntimeError("No se encontraron bytes válidos para cargar")

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
                    raise RuntimeError(
                        f"Error al cargar: {self.gestor.obtener_ultimo_error()}"
                    )

        except Exception as e:
            raise RuntimeError(f"Error en cargador: {e}")

    def _cargar_directo_en_ram(self, datos: bytearray, base_addr: int) -> None:
        """
        Carga datos directamente en RAM (para zonas de sistema).
        
        Args:
            datos: Bytes a cargar
            base_addr: Dirección base
        """
        ram.write(base_addr, bytes(datos))

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
                        # Permitir tokens de longitud par hasta 16 (8 bytes)
                        if not re.fullmatch(r"[0-9A-Fa-f]+", t) or len(t) % 2 != 0 or len(t) > 16:
                            raise ValueError(f"Token hex inválido: {t}")

                        # Partir en bytes (pares de 2)
                        for i in range(0, len(t), 2):
                            byte_str = t[i:i+2]
                            line_bytes.append(int(byte_str, 16))

                    elif mode == "bin":
                        if not re.fullmatch(r"[01]{1,8}", t):
                            raise ValueError(f"Token binario inválido: {t}")
                        line_bytes.append(int(t, 2))

                    elif mode == "dec":
                        val = int(t)
                        if not (0 <= val <= 255):
                            raise ValueError(f"Valor fuera de rango: {val}")
                        line_bytes.append(val)

                    else:
                        raise ValueError(f"Modo de lectura inválido: {mode}")

                except ValueError as e:
                    raise ValueError(
                        f"Línea {idx+1}: token '{t}' inválido en modo {mode} - {e}"
                    )

            # Validar límite de bytes
            if len(line_bytes) > bytes_per_line:
                raise ValueError(
                    f"Línea {idx+1} excede {bytes_per_line} bytes."
                )

            # Rellenar con ceros hasta completar bytes_per_line
            while len(line_bytes) < bytes_per_line:
                line_bytes.append(0)

            parsed_bytes.extend(line_bytes)

        return parsed_bytes

    def _crear_modulo_objeto(self, codigo_bytes: bytearray, base_addr: int) -> str:
        """
        Crea un módulo objeto en formato de texto a partir de bytes.
        
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
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        except Exception as e:
            raise RuntimeError(f"Error al leer archivo: {e}")


# Instancia global del cargador
loader_txt = LoaderTxt()
