"""
Módulo Enlazador-Cargador del CacaoCore-64
============================================

API unificada para enlazar y cargar programas.

Importación simple:
    from enlazador_cargador import Linker, LinkerError, loader_txt
    
    linker = Linker()
    output = linker.link_and_load(reloc_text, 0x00001000)
"""

from .linker import Linker, LinkerError
from .loader_txt import loader_txt
from .gestor_enlazador_cargador import GestorEnlazadorCargador
from .enlazador import Enlazador, BinarioEjectable, ErrorEnlazador
from .cargador import CargadorMejorado, ErrorCargador

__all__ = [
    # Main API (usable directly)
    'Linker',
    'LinkerError',
    'loader_txt',
    
    # Advanced API (para uso avanzado)
    'GestorEnlazadorCargador',
    'Enlazador',
    'BinarioEjectable',
    'CargadorMejorado',
    'ErrorEnlazador',
    'ErrorCargador',
]
