
# `src/isa/` — Especificaciones de la ISA

Breve descripción del fichero `microinstructions.py` que define las
microinstrucciones del simulador de 64 bits.

Descripción
-----------
`microinstructions.py` expone la lista `MICROINSTRUCTION_SPECS`: una lista
de diccionarios donde cada entrada tiene al menos las claves `name` y
`opcode`. Los `opcode` son enteros (normalmente expresados en hexadecimal)
que identifican la instrucción a 64 bits.

Convenciones
-----------
- Los opcodes están definidos como enteros de 64 bits (hex).  
- Los 2 bits menos significativos codifican el modo de direccionamiento:
	registro (`r` = 0b00), inmediato (`i` = 0b01), memoria (`m` = 0b10)
	y ninguno/especial (`n` = 0b11).
- Los nombres de instrucción siguen el patrón descriptivo (por ejemplo
	`add_rr`, `movd_rm`, `jmp_m`).

Uso
-----
- El decodificador importa `MICROINSTRUCTION_SPECS` para construir el árbol
	de decodificación y mapear opcodes a nombres y formatos.
- Para inspeccionar o ampliar el conjunto de instrucciones, editar
	[src/isa/microinstructions.py](microinstructions.py).

Buenas prácticas
---------------
- Mantener nombres únicos y opcodes no colisionantes.  
- Documentar cualquier nueva instrucción en `microinstructions.py` y, si
	procede, actualizar el decodificador (`src/processor/decoder.py`).

Referencias
----------
- Entrada principal: [src/isa/microinstructions.py](microinstructions.py)
- Export: [src/isa/__init__.py](__init__.py)

