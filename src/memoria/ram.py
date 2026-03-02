"""
ram.py — Memoria Principal (RAM) del Computador Simulado de 64 bits
====================================================================
Capacidad : 1 MB  (1 048 576 bytes), byte-addressable.
Palabras  : 64 bits = 8 bytes consecutivos, acceso ALINEADO (dir % 8 == 0).
Endianness: little-endian (byte de menor peso en la dirección menor).

Mapa de memoria (direcciones de 32 bits):
  0x00000000 – 0x00000FFF   4 KB   Sistema / vectores   (reservado)
  0x00001000 – 0x0003FFFF 252 KB   Código del programa  (solo lectura en ejecución)
  0x00040000 – 0x0007FFFF 256 KB   Datos estáticos
  0x00080000 – 0x000BFFFF 256 KB   Heap  (crece hacia arriba)
  0x000C0000 – 0x000FFFFF 256 KB   Pila  (crece hacia abajo, SP inicial = 0x000FFFFF)
"""

import struct


# ---------------------------------------------------------------------------
# Constantes del mapa de memoria
# ---------------------------------------------------------------------------

RAM_SIZE       = 1 * 1024 * 1024        # 1 MB

# Límites de zona (inclusive inicio, EXCLUSIVE fin)
SYS_START      = 0x00000000
VECTOR_TABLE   = 0x00000010             # Base de la tabla de vectores de interrupción
SYS_END        = 0x00001000             # 4 KB reservados para el simulador

CODE_START     = 0x00001000             # PC arranca aquí
CODE_END       = 0x00040000             # 252 KB de código

DATA_START     = 0x00040000             # Datos estáticos / globales
DATA_END       = 0x00080000             # 256 KB

HEAP_START     = 0x00080000             # Heap — crece ↑
HEAP_END       = 0x000C0000             # 256 KB

STACK_START    = 0x000C0000             # Base de la pila
STACK_END      = 0x00100000             # 256 KB (SP inicial = STACK_END - 1)
SP_INITIAL     = STACK_END - 1          # 0x000FFFFF

WORD_SIZE      = 8                      # bytes por palabra de 64 bits
PC_INITIAL     = CODE_START             # 0x00001000


# ---------------------------------------------------------------------------
# Excepciones específicas de RAM
# ---------------------------------------------------------------------------

class RAMError(Exception):
    """Error base para operaciones sobre la RAM."""

class AddressOutOfRange(RAMError):
    """Dirección fuera del espacio de 1 MB."""

class AlignmentError(RAMError):
    """Acceso de 64 bits no alineado a múltiplo de 8."""

class WriteProtectionError(RAMError):
    """Intento de escritura en la zona de código con protección activa."""

class InvalidSizeError(RAMError):
    """Tamaño de lectura/escritura inválido o excede el límite de la RAM."""


# ---------------------------------------------------------------------------
# Clase RAM
# ---------------------------------------------------------------------------

class RAM:
    """
    Memoria principal del computador simulado.

    Uso típico
    ----------
        ram = RAM()
        ram.write(CODE_START, bytes([...]))   # el enlazador deposita instrucciones
        word = ram.read_word(CODE_START)      # la CPU hace fetch
        ram.write_word(DATA_START, 42)        # escribe variable global

    Protección de escritura
    -----------------------
        ram.protect_code()    →  activa  (modo ejecución)
        ram.unprotect_code()  →  desactiva (modo carga del enlazador)
    """

    def __init__(self):
        self._mem: bytearray = bytearray(RAM_SIZE)
        self._code_protected: bool = False   # False mientras el enlazador carga

    # ------------------------------------------------------------------
    # Control de protección de zona de código
    # ------------------------------------------------------------------

    def protect_code(self) -> None:
        """
        Activa la protección de escritura sobre la zona de código
        (0x00001000 – 0x0003FFFF).  Debe llamarse DESPUÉS de que el
        enlazador haya depositado todas las instrucciones.
        """
        self._code_protected = True

    def unprotect_code(self) -> None:
        """
        Desactiva la protección de escritura (modo carga del enlazador).
        """
        self._code_protected = False

    @property
    def code_protected(self) -> bool:
        return self._code_protected

    # ------------------------------------------------------------------
    # Validaciones internas
    # ------------------------------------------------------------------

    def _check_bounds(self, addr: int, size: int) -> None:
        """Verifica que [addr, addr+size) esté dentro del espacio de 1 MB."""
        if addr < 0 or size <= 0:
            raise AddressOutOfRange(
                f"Dirección o tamaño inválido: addr=0x{addr:08X}, size={size}"
            )
        if addr + size > RAM_SIZE:
            raise AddressOutOfRange(
                f"Acceso fuera de rango: 0x{addr:08X} + {size} bytes "
                f"excede RAM_SIZE (0x{RAM_SIZE:08X})"
            )

    def _check_alignment(self, addr: int) -> None:
        """Verifica alineación a 8 bytes para acceso de palabra de 64 bits."""
        if addr % WORD_SIZE != 0:
            raise AlignmentError(
                f"Acceso no alineado: 0x{addr:08X} no es múltiplo de {WORD_SIZE}"
            )

    def _check_write_protection(self, addr: int, size: int) -> None:
        """Lanza excepción si se intenta escribir en la zona de código protegida."""
        if not self._code_protected:
            return
        # ¿El rango [addr, addr+size) se solapa con [CODE_START, CODE_END)?
        if addr < CODE_END and addr + size > CODE_START:
            raise WriteProtectionError(
                f"Escritura denegada en zona de código: "
                f"0x{addr:08X} – 0x{addr+size-1:08X}"
            )

    # ------------------------------------------------------------------
    # Interfaz pública — acceso a bytes
    # ------------------------------------------------------------------

    def read(self, addr: int, size: int) -> bytes:
        """
        Lee `size` bytes a partir de `addr`.

        Parámetros
        ----------
        addr : int   Dirección de inicio (0 – 0x000FFFFF).
        size : int   Número de bytes a leer (≥ 1).

        Retorna
        -------
        bytes        Copia de los bytes leídos.

        Ejemplo
        -------
            instr_bytes = ram.read(CODE_START, 8)   # primera instrucción
        """
        self._check_bounds(addr, size)
        return bytes(self._mem[addr : addr + size])

    def write(self, addr: int, data: bytes | bytearray) -> None:
        """
        Escribe los bytes de `data` a partir de `addr`.

        Parámetros
        ----------
        addr : int                  Dirección de inicio.
        data : bytes | bytearray    Datos a escribir.

        Ejemplo
        -------
            ram.write(CODE_START, encoded_instructions)
        """
        size = len(data)
        if size == 0:
            return
        self._check_bounds(addr, size)
        self._check_write_protection(addr, size)
        self._mem[addr : addr + size] = data

    # ------------------------------------------------------------------
    # Interfaz pública — acceso a palabras de 64 bits
    # ------------------------------------------------------------------

    def read_word(self, addr: int) -> int:
        """
        Lee una palabra de 64 bits (little-endian) desde `addr`.
        La dirección DEBE ser múltiplo de 8.

        Parámetros
        ----------
        addr : int   Dirección alineada (addr % 8 == 0).

        Retorna
        -------
        int          Valor entero sin signo de 64 bits.

        Ejemplo
        -------
            valor = ram.read_word(DATA_START)
        """
        self._check_alignment(addr)
        self._check_bounds(addr, WORD_SIZE)
        (value,) = struct.unpack_from("<Q", self._mem, addr)
        return value

    def write_word(self, addr: int, value: int) -> None:
        """
        Escribe una palabra de 64 bits (little-endian) en `addr`.
        La dirección DEBE ser múltiplo de 8.

        Parámetros
        ----------
        addr  : int   Dirección alineada (addr % 8 == 0).
        value : int   Valor entero sin signo de 64 bits (0 – 2^64-1).

        Ejemplo
        -------
            ram.write_word(DATA_START, 0xDEADBEEFCAFEBABE)
        """
        self._check_alignment(addr)
        self._check_bounds(addr, WORD_SIZE)
        self._check_write_protection(addr, WORD_SIZE)
        if not (0 <= value < 2**64):
            raise ValueError(
                f"Valor fuera del rango de 64 bits: {value}"
            )
        struct.pack_into("<Q", self._mem, addr, value)

    # ------------------------------------------------------------------
    # Utilidades de diagnóstico
    # ------------------------------------------------------------------

    def dump(self, addr: int, size: int, bytes_per_row: int = 16) -> str:
        """
        Retorna un volcado hexadecimal de `size` bytes a partir de `addr`.
        Útil para depuración desde el REPL o logs del simulador.

        Ejemplo
        -------
            print(ram.dump(CODE_START, 64))
        """
        self._check_bounds(addr, size)
        lines = []
        for offset in range(0, size, bytes_per_row):
            row_addr = addr + offset
            chunk = self._mem[row_addr : row_addr + bytes_per_row]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            asc_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"0x{row_addr:08X}  {hex_part:<{bytes_per_row*3}}  {asc_part}")
        return "\n".join(lines)

    def zone_of(self, addr: int) -> str:
        """
        Retorna el nombre de la zona de memoria a la que pertenece `addr`.
        Útil para mensajes de error del simulador.
        """
        if SYS_START <= addr < SYS_END:
            return "SISTEMA"
        if CODE_START <= addr < CODE_END:
            return "CÓDIGO"
        if DATA_START <= addr < DATA_END:
            return "DATOS ESTÁTICOS"
        if HEAP_START <= addr < HEAP_END:
            return "HEAP"
        if STACK_START <= addr < STACK_END:
            return "PILA"
        return "FUERA DE RANGO"

    def __repr__(self) -> str:
        return (
            f"<RAM size=1MB code_protected={self._code_protected} "
            f"hex_layout="
            f"SYS:0x{SYS_START:05X}-0x{SYS_END-1:05X} "
            f"CODE:0x{CODE_START:05X}-0x{CODE_END-1:05X} "
            f"DATA:0x{DATA_START:05X}-0x{DATA_END-1:05X} "
            f"HEAP:0x{HEAP_START:05X}-0x{HEAP_END-1:05X} "
            f"STACK:0x{STACK_START:05X}-0x{STACK_END-1:05X}>"
        )


# ---------------------------------------------------------------------------
# Instancia global compartida (importar desde cualquier módulo del proyecto)
# ---------------------------------------------------------------------------

ram = RAM()
