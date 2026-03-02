"""Processor Module
=================

Núcleo del procesador Cacao Core 64.

Contiene la Unidad de Control, la Unidad Aritmético-Lógica, el Decodificador
y todos los componentes necesarios para ejecutar instrucciones según la ISA.

Módulos
-------
control_unit : Unidad de Control principal.
alu : Unidad Aritmético-Lógica.
decoder : Decodificador de instrucciones ISA.

Exportados
----------
ControlUnit : Clase principal de la Unidad de Control.
"""

from .control_unit import ControlUnit