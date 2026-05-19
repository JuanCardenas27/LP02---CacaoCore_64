class GestorRegistros:
    def __init__(self):
        # Usamos de R0 a R12 (13 registros disponibles)
        self.registros = {f"R{i}": False for i in range(13)}
        self.acumulador = "R15"

    def ocupar(self):
        for reg, ocupado in self.registros.items():
            if not ocupado:
                self.registros[reg] = True
                return reg
        raise Exception("¡Derrame de registros! (Register Spill): No hay registros libres.")

    def liberar(self, reg):
        if reg in self.registros:
            self.registros[reg] = False

    def liberar_todo(self):
        for reg in self.registros:
            self.registros[reg] = False
