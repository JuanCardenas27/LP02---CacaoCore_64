# Computador Simulado de 64 bits

Simulador de un computador de propósito general de **64 bits** implementado en Python.  
Arquitectura: CPU → RAM → ejecución.

---

## Estructura del proyecto

```
simulador/
├── README.md                        ← Este archivo (visión general)
├── jerarquia_memoria.md             ← Documento de diseño completo del sistema
│
├── src/
│   ├── memoria/
│   │   ├── ram.py                   ← Memoria principal (1 MB)
│   │   └── README.md                ← Documentación detallada de la RAM
│   ├── processor/
│   │   ├── processor.py             ← CPU y banco de registros
│   │   ├── alu.py                   ← Unidad Aritmético-Lógica
│   │   └── README.md                ← 🔧 Pendiente — Documentación CPU
│   ├── enlazador_cargador/
│   │   ├── enlazador.py             ← Resuelve símbolos y genera binario
│   │   ├── cargador.py              ← Carga binario en RAM e inicializa entorno
│   │   └── binario.py               ← Estructura del binario ejecutable
│   └── isa/
│       └── README.md                ← 🔧 Pendiente — Opcodes y codificación
│
├── tests/
│   └── README.md                    ← 🔧 Pendiente — Pruebas unitarias
│
└── programas/                       ← Binarios compilados (.bin)
```

---

## Módulos

###  `src/memoria/` — RAM
Memoria principal de 1 MB dividida en cinco zonas fijas.  
Ver documentación completa en [src/memoria/README.md](src/memoria/README.md).

| Zona            | Rango                     | Tamaño |
|-----------------|---------------------------|--------|
| Sistema         | `0x00000000 – 0x00000FFF` | 4 KB   |
| Código          | `0x00001000 – 0x0003FFFF` | 252 KB |
| Datos estáticos | `0x00040000 – 0x0007FFFF` | 256 KB |
| Heap            | `0x00080000 – 0x000BFFFF` | 256 KB |
| Pila            | `0x000C0000 – 0x000FFFFF` | 256 KB |

Importar desde cualquier módulo:
```python
from src.memoria.ram import ram, CODE_START, DATA_START, WORD_SIZE
```

### `src/processor/` — CPU y ALU
Procesador de 64 bits con 16 registros de propósito general.
- `processor.py`: Unidad de Control, banco de registros (PC, SP, ACC, FLAGS, etc.)
- `alu.py`: Operaciones aritméticas, lógicas, comparaciones y desplazamientos

### `src/enlazador_cargador/` — Enlazador y Cargador
Resuelve símbolos, genera binarios ejecutables y carga programas en memoria.
- `enlazador.py`: Resuelve referencias externas, unifica segmentos, genera binario absoluto
- `cargador.py`: Valida memoria, copia código/datos, inicializa registros y entorno
- `binario.py`: Estructura y serialización del binario ejecutable

