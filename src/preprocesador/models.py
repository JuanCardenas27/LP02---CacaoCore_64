from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .errors import MacroError


@dataclass
class SourceLine:
    """Rastrea el origen de cada linea de salida (para mensajes de error)."""

    path: str
    line: int


@dataclass
class PreprocessResult:
    """Resultado completo del preprocesado."""

    text: str
    line_map: List[SourceLine]
    exports: Optional[Dict[str, Set[str]]] = None
    internals: Optional[Dict[str, Set[str]]] = None
    imports: Optional[Dict[str, Set[str]]] = None

@dataclass
class PreprocessMetadata:
    """Resultado completo del preprocesado."""

    lista: List[str]
    line_map: List[SourceLine]


@dataclass
class Macro:
    """Representa una macro definida con #define."""

    nombre: str
    valor: str
    parametros: Optional[List[str]] = None

    @staticmethod
    def _es_inicio_identificador(caracter: str) -> bool:
        return caracter.isalpha() or caracter == "_"

    @staticmethod
    def _es_identificador(caracter: str) -> bool:
        return caracter.isalnum() or caracter == "_"

    def _reemplazar_identificadores(self, texto: str, reemplazos: dict) -> str:
        resultado: List[str] = []
        indice = 0

        while indice < len(texto):
            caracter = texto[indice]
            if self._es_inicio_identificador(caracter):
                inicio = indice
                indice += 1
                while indice < len(texto) and self._es_identificador(texto[indice]):
                    indice += 1
                identificador = texto[inicio:indice]
                resultado.append(reemplazos.get(identificador, identificador))
                continue

            resultado.append(caracter)
            indice += 1

        return "".join(resultado)

    def expandir(self, argumentos: Optional[List[str]] = None) -> str:
        if self.parametros is None:
            return self.valor

        n_esp = len(self.parametros)
        n_rec = len(argumentos) if argumentos else 0
        if argumentos is None or n_rec != n_esp:
            raise MacroError(
                f"Macro '{self.nombre}' espera {n_esp} argumento(s), "
                f"se recibieron {n_rec}"
            )

        reemplazos = {
            param: arg.strip() for param, arg in zip(self.parametros, argumentos)
        }
        return self._reemplazar_identificadores(self.valor, reemplazos)

    def __repr__(self) -> str:
        if self.parametros is not None:
            return (f"Macro({self.nombre}"
                    f"({','.join(self.parametros)}) = {self.valor})")
        return f"Macro({self.nombre} = {self.valor})"
