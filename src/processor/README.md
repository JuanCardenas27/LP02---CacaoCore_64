# Processor Module - Cacao Core 64

Núcleo del procesador Cacao Core 64. Este módulo implementa la arquitectura del procesador incluyendo la Unidad de Control, la Unidad Aritmético-Lógica y el Decodificador de instrucciones.

## Descripción General

El módulo `processor` contiene los componentes principales del procesador:

- **Unidad de Control (Control Unit)**: Gestiona el flujo de ejecución, fetch-decode-execute, y manejo de interrupciones.
- **Unidad Aritmético-Lógica (ALU)**: Realiza operaciones aritméticas, lógicas y de desplazamiento.
- **Decodificador (Decoder)**: Convierte instrucciones binarias en nombres de microinstrucciones según la ISA.

## Componentes

### 1. Unidad de Control (`control_unit.py`)

La Unidad de Control (CU) es el corazón del procesador. Gestiona:

- **Ciclo de ejecución**: Fetch → Decode → Execute
- **Registros**: 16 registros de propósito general + registros especiales (PC, IR, MAR, MDR, FR, DP)
- **Memoria**: Lectura/escritura de datos en RAM
- **Interrupciones**: Manejo de interrupciones (INTR, INTA)
- **Stack**: Operaciones de push/pop mediante registro SP

**Registros especiales:**
- `_pc` (Program Counter): Dirección de la siguiente instrucción (8 bytes)
- `_ir` (Instruction Register): Instrucción actual (8 bytes)
- `_mar` (Memory Address Register): Dirección para acceso a memoria (4 bytes)
- `_mdr` (Memory Data Register): Datos leídos/escritos (6 bytes)
- `_fr` (Flags Register): Banderas de estado (1 byte)
- `_dp` (Decode Pointer): Puntero de decodificación (1 byte)

**Banderas (_fr):**
- Bit 0: Interrupt Enable (I)
- Bit 1: Overflow (V)
- Bit 2: Carry (C)
- Bit 3: Negative (N)
- Bit 4: Zero (Z)

**Estados:**
- `RUNNING (1)`: Procesador ejecutando instrucciones
- `HALTED (0)`: Procesador detenido

### 2. Unidad Aritmético-Lógica (`alu.py`)

La ALU ejecuta operaciones en operandos de 64 bits y mantiene flags de estado.

**Operaciones Aritméticas:**
- `add()` - Suma (actualiza overflow y carry)
- `sub()` - Resta
- `mul()` - Multiplicación
- `div()` - División entera (devuelve residuo)
- `inc()` - Incremento
- `dec()` - Decremento

**Operaciones Lógicas:**
- `and_a()` - AND
- `or_a()` - OR
- `xor_a()` - XOR
- `not_a()` - NOT

**Operaciones de Desplazamiento:**
- `shl()` - Shift Left (desplazamiento a izquierda)
- `shr()` - Shift Right (desplazamiento a derecha)

**Operaciones de Comparación:**
- `cmp()` - Compara dos operandos (resta sin guardar resultado)
- `test()` - AND lógico sin guardar resultado

### 3. Decodificador (`decoder.py`)

Convierte secuencias de bytes en nombres de instrucciones según la ISA.

**Características:**
- Construcción de árbol de decodificación nibble-based (4 bits por nivel)
- Detección automática de colisiones de opcodes
- Incremento automático del Decode Pointer (DP)
- Manejo de errores para opcodes inválidos

**Excepciones:**
- `DecoderException`: Clase base para errores del decodificador
- `ISAOpcodesCollision`: Conflicto entre opcodes (prefijos superpuestos, duplicados)
- `InvalidOpcode`: Opcode inválido o inexistente

## Uso

### Inicializar el Procesador

```python
from processor import ControlUnit

# Crear instancia de la Unidad de Control
cu = ControlUnit()

# Inicializar el sistema (Power-On Reset)
cu._boot(start_address=0)

# 0 es la dirección inicial del PC
```

### Ejecutar Instrucciones

```python
# Modo: Ejecución completa
cu._run_full_exec()

# Modo: Ejecución paso a paso
cu._run_step()
```

### Trabajar con la ALU

```python
from processor.alu import ALU

# Crear instancia
acumulador = bytearray(8)
flags = bytearray(1)
alu = ALU(acumulador, flags)

# Operandos
op1 = bytearray((5).to_bytes(8, byteorder='little', signed=True))
op2 = bytearray((3).to_bytes(8, byteorder='little', signed=True))

# Ejecutar operación
alu.add(op1, op2)

# Resultados
print(f"Acumulador: {int.from_bytes(acumulador, byteorder='little', signed=True)}")
print(f"Flags: {bin(int.from_bytes(flags, byteorder='little'))}")
```

### Decodificar Instrucciones

```python
from processor.decoder import Decoder

dp = bytearray([0])
decoder = Decoder(dp)

instruction_bytes = bytearray([0x12, 0x34])  # Ejemplo
try:
    instr_name = decoder.decode(instruction_bytes)
    print(f"Instrucción: {instr_name}")
except Exception as e:
    print(f"Error: {e}")
```

## Arquitectura

```
┌─────────────────────────────────────┐
│        Control Unit (CU)            │
├─────────────────────────────────────┤
│ • 16 Registros de propósito general │
│ • Registros especiales (PC, IR, etc)│
│ • Ciclo fetch-decode-execute        │
│ • Manejo de interrupciones          │
└────────┬──────────────────┬─────────┘
         │                  │
    ┌────▼────────┐  ┌──────▼─────┐
    │    ALU       │  │  Decoder   │
    ├─────────────┤  ├────────────┤
    │ Aritmética  │  │ ISA Parser  │
    │ Lógica      │  │ Opcode Tree │
    │ Desplazam.  │  └────────────┘
    │ Banderas    │       │
    └─────────────┘       │
         │                │
         └────────┬───────┘
                  │
            ┌─────▼─────┐
            │    RAM     │
            └────────────┘
```

## Flujo de Ejecución

1. **FETCH**: Lectura de instrucción desde RAM
2. **DECODE**: Decodificación a nombre de microinstrucción
3. **EXECUTE**: Ejecución de microinstrucción
4. **CHECK_INTP**: Verificación de interrupciones pendientes

## Flags y Estados

Las banderas se actualizan automáticamente según los resultados de las operaciones ALU:

- **Zero (Z)**: Se activa si el resultado es cero
- **Negative (N)**: Se activa si el resultado es negativo
- **Overflow (V)**: Se activa en overflow aritmético
- **Carry (C)**: Se activa en carry de la operación más significativa
- **Interrupt (I)**: Habilita/deshabilita interrupciones

## Ejemplo Completo

```python
from processor import ControlUnit

# Inicializar
cu = ControlUnit()
cu._boot(start_address=0)

# Cargar programa en memoria (simulado)
# Aquí irían las instrucciones del programa

# Ejecutar
cu._run_full_exec()
```

## Notas Importantes

- Las operaciones usan **little-endian** para conversión de bytes
- Los operandos son de **64 bits** (8 bytes)
- El acumulador (registro 15) es de lectura/escritura a través de la ALU
- Las interrupciones deben habilitarse con `ei()` y deshabilitarse con `di()`
- El Stack Pointer está en el registro 13 (R13)
- Link Register en registro 14 (R14)

## Dependencias

- `memoria.ram`: Módulo de memoria RAM
- `isa.microinstructions`: Definiciones de microinstrucciones ISA

## Archivos

- `control_unit.py`: Implementación de la Unidad de Control
- `alu.py`: Implementación de la ALU
- `decoder.py`: Implementación del Decodificador
- `__init__.py`: Exportaciones del módulo
