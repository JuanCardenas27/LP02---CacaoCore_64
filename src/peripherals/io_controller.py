from memoria.ram import ram

# Códigos de acción
CONSOLE_CODE = 0


class IOController:

    def __init__(self):
        self._handlers = {
            CONSOLE_CODE: self._consola_escribir,
        }
        self.console = None     # Asignada desde main

    def handle_interrupt(self, vector: bytearray, registers: list) -> None:
        vector = int.from_bytes(vector,byteorder="little", signed=False)
        handler = self._handlers.get(vector)
        if handler:
            handler(registers)
        else:
            print(f"[Controlador I/O] Vector {vector} sin manejador registrado.")

    # ------------------------------------------------------------------
    # Manejadores Python-side de cada periférico
    # ------------------------------------------------------------------

    def _consola_escribir(self, registers: list) -> None:
        addr   = int.from_bytes(registers[0], byteorder='little', signed=False)
        length = int.from_bytes(registers[1], byteorder='little', signed=False)

        if length == 0:
            return

        data = ram.read(addr, length) # TODO: Agregar formato.
        self.console.write_ok(int.from_bytes(data, byteorder="little", signed=False))


# ------------------------------------------------------------------
# Instancia global
# ------------------------------------------------------------------

io_controller = IOController()