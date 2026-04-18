class PreprocesadorError(Exception):
    """Base de todos los errores del preprocesador."""

    def __init__(self, mensaje: str, archivo: str = None, linea: int = None):
        self.archivo = archivo
        self.linea = linea
        ubicacion = f"{archivo}:{linea}" if archivo else "<desconocido>"
        super().__init__(f"[PREPROCESADOR] {ubicacion}: {mensaje}")


class IncludeError(PreprocesadorError):
    """Error al resolver o leer un #include."""


class MacroError(PreprocesadorError):
    """Error en la definicion o expansion de una macro."""


class CondicionalError(PreprocesadorError):
    """Error en bloques #ifdef / #ifndef / #else / #endif."""
