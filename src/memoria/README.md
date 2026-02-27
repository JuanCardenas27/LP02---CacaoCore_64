# `src/memoria/` — Módulo de memoria principal

Documentación del módulo `ram.py` del Computador Simulado de 64 bits.

### Descripción general

La RAM es la memoria principal del simulador. Internamente es un `bytearray` de **1 MB** (1 048 576 bytes) dividido en zonas fijas.

Cada posición almacena **1 byte**. Una palabra de 64 bits ocupa **8 bytes consecutivos** y debe estar alineada a múltiplos de 8. El orden de bytes es **little-endian**.

```
Enlazador ──escribe──► RAM
                        │
CPU (fetch) ◄──lee──── RAM
CPU (write) ───escribe─► RAM
```

---

### Mapa de memoria

```
 Dirección inicio   Dirección fin    Tamaño     Zona
 ────────────────   ─────────────    ───────    ─────────────────────
 0x00000000         0x00000FFF         4 KB     Sistema / vectores   (reservado)
 0x00001000         0x0003FFFF       252 KB     Código del programa
 0x00040000         0x0007FFFF       256 KB     Datos estáticos
 0x00080000         0x000BFFFF       256 KB     Heap
 0x000C0000         0x000FFFFF       256 KB     Pila (Stack)
```

#### Zona: Sistema / vectores (`0x00000000 – 0x00000FFF`)
Reservada para el simulador. El PC nunca apunta aquí durante la ejecución normal.

#### Zona: Código del programa (`0x00001000 – 0x0003FFFF`)
El enlazador deposita aquí las instrucciones compiladas en binario de 64 bits. El **PC arranca en `0x00001000`** y avanza de 8 en 8 bytes (`PC += 8`) en cada fetch. Capacidad máxima: ~31 500 instrucciones.

Una vez que el enlazador termina, llama a `ram.protect_code()` para activar la **protección de escritura**: cualquier intento posterior de escribir en esta zona lanza `WriteProtectionError`.

#### Zona: Datos estáticos (`0x00040000 – 0x0007FFFF`)
Variables globales y constantes del programa. El enlazador deposita los valores iniciales. La CPU puede leer y escribir libremente durante la ejecución.

#### Zona: Heap (`0x00080000 – 0x000BFFFF`)
Memoria dinámica. Crece **hacia arriba** (direcciones crecientes) desde `HEAP_START`.

#### Zona: Pila / Stack (`0x000C0000 – 0x000FFFFF`)
Variables locales y direcciones de retorno. Crece **hacia abajo**. El **SP se inicializa en `0x000FFFFF`**. Cada `PUSH` decrementa el SP antes de escribir; cada `POP` lee y luego incrementa el SP.

---

### Constantes exportadas

```python
from src.memoria.ram import (
    RAM_SIZE, WORD_SIZE,
    SYS_START,   SYS_END,
    CODE_START,  CODE_END,
    DATA_START,  DATA_END,
    HEAP_START,  HEAP_END,
    STACK_START, STACK_END,
    SP_INITIAL,  PC_INITIAL,
)
```

| Constante     | Valor         | Descripción |
|---------------|---------------|-------------|
| `RAM_SIZE`    | `1 048 576`   | Tamaño total de la RAM en bytes (1 MB). |
| `WORD_SIZE`   | `8`           | Bytes por palabra de 64 bits. |
| `SYS_START`   | `0x00000000`  | Inicio de la zona de sistema. |
| `SYS_END`     | `0x00001000`  | Fin exclusivo de la zona de sistema. |
| `CODE_START`  | `0x00001000`  | Inicio de la zona de código. PC arranca aquí. |
| `CODE_END`    | `0x00040000`  | Fin exclusivo de la zona de código. |
| `DATA_START`  | `0x00040000`  | Inicio de datos estáticos. |
| `DATA_END`    | `0x00080000`  | Fin exclusivo de datos estáticos. |
| `HEAP_START`  | `0x00080000`  | Inicio del heap. |
| `HEAP_END`    | `0x000C0000`  | Fin exclusivo del heap. |
| `STACK_START` | `0x000C0000`  | Inicio (base) de la pila. |
| `STACK_END`   | `0x00100000`  | Fin exclusivo de la pila. |
| `SP_INITIAL`  | `0x000FFFFF`  | Valor inicial del Stack Pointer (`STACK_END - 1`). |
| `PC_INITIAL`  | `0x00001000`  | Valor inicial del Program Counter (`CODE_START`). |

---

### Excepciones

```python
from src.memoria.ram import (
    RAMError, AddressOutOfRange, AlignmentError,
    WriteProtectionError, InvalidSizeError,
)
```

| Excepción              | Cuándo se lanza |
|------------------------|-----------------|
| `RAMError`             | Clase base. No se lanza directamente. |
| `AddressOutOfRange`    | `addr < 0` o `addr + size > RAM_SIZE`. |
| `AlignmentError`       | `addr % 8 != 0` en `read_word()` o `write_word()`. |
| `WriteProtectionError` | Escritura en la zona de código mientras la protección está activa. |
| `InvalidSizeError`     | Tamaño de lectura/escritura inválido (≤ 0). |

---

### Métodos

#### `read(addr, size) → bytes`

Lee `size` bytes crudos a partir de `addr`. Devuelve una copia como `bytes`.

```python
instr_bytes = ram.read(CODE_START, 8)    # primera instrucción
datos       = ram.read(DATA_START, 16)   # 16 bytes de datos estáticos
```

| Parámetro | Tipo  | Descripción |
|-----------|-------|-------------|
| `addr`    | `int` | Dirección de inicio (0 – 0x000FFFFF). |
| `size`    | `int` | Número de bytes a leer (≥ 1). |

Lanza `AddressOutOfRange` si el rango excede la RAM.

---

#### `write(addr, data)`

Escribe los bytes de `data` a partir de `addr`. Acepta `bytes` o `bytearray`.

```python
ram.write(CODE_START, instrucciones_compiladas)
ram.write(DATA_START, datos_iniciales)
```

| Parámetro | Tipo                  | Descripción |
|-----------|-----------------------|-------------|
| `addr`    | `int`                 | Dirección de inicio. |
| `data`    | `bytes` / `bytearray` | Datos a escribir. |

Lanza `AddressOutOfRange` si el rango excede la RAM.  
Lanza `WriteProtectionError` si la zona de código está protegida.

---

#### `read_word(addr) → int`

Lee una **palabra de 64 bits** (little-endian) desde `addr`. La dirección debe ser múltiplo de 8. Retorna un entero sin signo de 64 bits (0 – 2⁶⁴ − 1).

```python
instruccion = ram.read_word(pc)          # fetch de la CPU
valor       = ram.read_word(DATA_START)  # leer variable global
```

| Parámetro | Tipo  | Descripción |
|-----------|-------|-------------|
| `addr`    | `int` | Dirección alineada a 8 bytes (`addr % 8 == 0`). |

Lanza `AlignmentError` si `addr % 8 != 0`.  
Lanza `AddressOutOfRange` si el rango excede la RAM.

---

#### `write_word(addr, value)`

Escribe una **palabra de 64 bits** (little-endian) en `addr`. La dirección debe ser múltiplo de 8.

```python
ram.write_word(DATA_START, resultado)    # guardar variable global

sp -= WORD_SIZE
ram.write_word(sp, valor)               # PUSH al stack
```

| Parámetro | Tipo  | Descripción |
|-----------|-------|-------------|
| `addr`    | `int` | Dirección alineada a 8 bytes. |
| `value`   | `int` | Valor entero sin signo de 64 bits (0 – 2⁶⁴ − 1). |

Lanza `AlignmentError`, `AddressOutOfRange`, `WriteProtectionError` o `ValueError` según corresponda.

---

#### `protect_code()`

Activa la protección de escritura sobre la zona de código (`0x00001000 – 0x0003FFFF`). Llamar **después** de que el enlazador termine de cargar el programa.

```python
ram.write(CODE_START, instrucciones)
ram.protect_code()   # a partir de aquí, zona de código = solo lectura
```

---

#### `unprotect_code()`

Desactiva la protección de escritura. Permite al enlazador volver a escribir en la zona de código (por ejemplo, para recargar un programa).

```python
ram.unprotect_code()
ram.write(CODE_START, nuevo_programa)
ram.protect_code()
```

---

#### `code_protected` (propiedad)

`bool`. Indica si la zona de código está protegida actualmente.

```python
if ram.code_protected:
    print("Zona de código bloqueada")
```

---

#### `dump(addr, size, bytes_per_row=16) → str`

Retorna un volcado hexadecimal legible para depuración. Muestra dirección, bytes en hex y representación ASCII.

```python
print(ram.dump(CODE_START, 64))
# 0x00001000  44 33 22 11 00 00 00 00  D3"...
```

| Parámetro       | Tipo  | Default | Descripción |
|-----------------|-------|---------|-------------|
| `addr`          | `int` | —       | Dirección de inicio. |
| `size`          | `int` | —       | Número de bytes a volcar. |
| `bytes_per_row` | `int` | `16`    | Bytes mostrados por línea. |

---

#### `zone_of(addr) → str`

Retorna el nombre de la zona de memoria a la que pertenece `addr`. Útil para mensajes de error.

```python
ram.zone_of(CODE_START)   # → 'CÓDIGO'
ram.zone_of(DATA_START)   # → 'DATOS ESTÁTICOS'
ram.zone_of(HEAP_START)   # → 'HEAP'
ram.zone_of(STACK_START)  # → 'PILA'
ram.zone_of(0x0)          # → 'SISTEMA'
ram.zone_of(0x00200000)   # → 'FUERA DE RANGO'
```

---

### Instancia global

`ram.py` expone una **instancia única** lista para usar. Todos los módulos del proyecto deben importar esta misma instancia para compartir el mismo espacio de memoria.

```python
from src.memoria.ram import ram
```

No crear instancias adicionales de `RAM()` salvo para pruebas aisladas.

---

### Flujo de uso

#### El enlazador carga el programa

```python
from src.memoria.ram import ram, CODE_START, DATA_START

# La protección está desactivada por defecto al crear la RAM
ram.write(CODE_START, instrucciones_en_bytes)    # binario compilado
ram.write(DATA_START, datos_estaticos_en_bytes)  # variables globales

ram.protect_code()   # bloquea zona de código antes de ejecutar
```

#### La CPU ejecuta

```python
from src.memoria.ram import ram, PC_INITIAL, SP_INITIAL, WORD_SIZE

pc = PC_INITIAL    # 0x00001000
sp = SP_INITIAL    # 0x000FFFFF

while True:
    instruccion = ram.read_word(pc)     # FETCH
    pc += WORD_SIZE

    # DECODE / EXECUTE (módulo CPU — a cargo de otro compañero)

    # Ejemplos de accesos a RAM que la CPU realiza:
    valor = ram.read_word(DATA_START + offset)      # leer variable global
    ram.write_word(DATA_START + offset, resultado)  # escribir variable global

    sp -= WORD_SIZE                                  # PUSH
    ram.write_word(sp, valor_a_apilar)

    valor = ram.read_word(sp)                        # POP
    sp += WORD_SIZE

    pc = direccion_destino                           # SALTO
```

---

### Reglas de acceso

| Regla | Detalle |
|-------|---------|
| **Alineación** | `read_word` y `write_word` requieren `addr % 8 == 0`. |
| **Endianness** | Little-endian. El byte de menor peso se guarda en la dirección más baja. |
| **Protección de código** | Después de `protect_code()`, no se puede escribir entre `CODE_START` y `CODE_END`. |
| **Una sola instancia** | Siempre `from src.memoria.ram import ram`. No crear `RAM()` adicionales en producción. |
| **Límites** | Todo acceso fuera de `[0, RAM_SIZE)` lanza `AddressOutOfRange`. |
