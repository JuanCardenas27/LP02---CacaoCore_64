import struct
from memoria.ram import ram, INTR_BUFFER

# Códigos de acción
CONSOLE_PRINT = 0x0

# Formatos de impresión
INT = 0x0
FLOAT = 0x1
STRING = 0x2
BOOL = 0x3


class IOController:

    _FORMAT_FUNCS = {
        INT: lambda x: int.from_bytes(x, byteorder="little", signed=True),
        FLOAT: lambda x: struct.unpack('<d', x)[0],
        STRING: lambda x: x.decode("utf-8", errors="surrogateescape"),
        BOOL: lambda x: "indeed" if bool(int.from_bytes(x, byteorder="little", signed=True)) else "nope"
    }

    def __init__(self):
        self.INTA = False
        self._handlers = {
            CONSOLE_PRINT: self._consola_escribir,
        }
        self.cu = None          # Asignada por la cu
        self.console = None     # Asignada desde main

    def handle_interrupt(self) -> None:
        """
        Maneja códigos de acción provocados por interrupciones de salida.
        """
        if self.INTA:
            self.INTA = False

            vector = ram.read(INTR_BUFFER, 1)
            vector = int.from_bytes(vector, byteorder="little", signed=False)
            handler = self._handlers.get(vector)
            if handler:
                handler(INTR_BUFFER + 1)
            else:
                print(f"[Controlador I/O] Código {vector} sin manejador registrado.")


    def send_interrupt(self, vector: bytearray):
        """
        Maneja buffering para que la unidad de control ejecute subrutinas de vectores.
        """
        ram.write(INTR_BUFFER, vector)  # Tamaño 1 byte
        self.cu.INTR = True


    # ------------------------------------------------------------------
    # Manejadores Python-side de cada periférico
    # ------------------------------------------------------------------

    def _consola_escribir(self, addr: int) -> None:
        length = ram.read(addr, 1)
        length = int.from_bytes(length, byteorder='little', signed=False)

        if length == 0:
            return
        
        format = ram.read(addr + 1, 1)
        format = int.from_bytes(format, byteorder='little', signed=False)

        format_func = self._FORMAT_FUNCS.get(format)
        if not format_func:
            print(f"[Controlador I/O] Formato {format} sin manejador registrado.")
            return
        
        if format == STRING:
            msg = []
            for i in range(length):
                data = ram.read(addr + 2 + i*8, 1)
                msg.append(format_func(data))
            self.console.write_ok("".join(msg))

        else:
            data = ram.read(addr + 2, length * 8)
            self.console.write_ok(format_func(data))


# ------------------------------------------------------------------
# Instancia global
# ------------------------------------------------------------------

io_controller = IOController()