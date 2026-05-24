# Imports desde codigo fuente (preprocesador)

Este documento describe el comportamiento actual del preprocesador para
importar funciones y variables desde archivos fuente no compilados, sin
romper el flujo existente de .import y .extern para librerias compiladas.

## Resumen

- `#include "archivo"` sigue funcionando para librerias compiladas
  (por ejemplo `utils.lib`, `math.lib`).
- Si el include apunta a un archivo fuente (por ejemplo `.txt`), el
  preprocesador lo procesa y expande en linea, con soporte de exports.
- Se agrego `#export` para declarar simbolos publicos en archivos fuente.

## Sintaxis

### Include de libreria compilada

```text
#include "utils.lib"
#include "math.lib" { VEC_MAX, VEC_SET }
```

Resultado (igual que antes):

```text
.import "utils.lib"
.extern VEC_MAX
.extern VEC_SET
```

### Include de archivo fuente

```text
#include "source_import_utils.txt" { max_of_three, total }
```

- Si el include es fuente, el preprocesador inserta el codigo del archivo
  incluido en la salida.
- La lista opcional `{ ... }` valida que esos simbolos existan y esten
  exportados en el archivo incluido.

### Export de simbolos

```text
#export { max_of_three, total }

func max_of_three(a: int, b: int, c: int) {
    // ...
}

let total: int = 0
```

Reglas:
- Si existe `#export`, solo esos simbolos son publicos.
- Si no hay `#export`, todos los `func` y `let` de nivel superior se
  consideran publicos por defecto.

## Resolucion de rutas

Para includes de fuente, el preprocesador busca el archivo en este orden:

1. Ruta relativa al archivo fuente actual (si el preprocesado conoce el path).
2. Subcarpetas de `src/examples` (recursivo).
3. Subcarpetas de `examples` (recursivo).

Si no se encuentra, se produce:

```
[PREPROCESADOR] <archivo>:<linea>: Archivo no encontrado: '...'
```

## Deteccion de ciclos

Si hay imports circulares entre archivos fuente, el preprocesador lanza
un error con el ciclo detectado.

## Conflictos de simbolos

Si dos archivos fuente exportan el mismo simbolo publico y ambos son
importados, se produce un error de conflicto.

## Integracion con GUI

- Cuando cargas un archivo con "Load file", el preprocesador usa esa ruta
  para resolver includes relativos.
- Si solo pegas texto en la GUI, el include se resuelve usando la busqueda
  en `src/examples`.

## Ejemplo minimo

Archivo: `source_import_utils.txt`

```text
#export { max_of_three, total }

func max_of_three(a: int, b: int, c: int) {
    if a > b {
        if a > c { deliver a } otherwise { deliver c }
    } otherwise {
        if b > c { deliver b } otherwise { deliver c }
    }
}

let total: int = 0
```

Archivo: `source_import_main.txt`

```text
#include "source_import_utils.txt" { max_of_three, total }

let a: int = 3
let b: int = 9
let c: int = 7

let m: int = max_of_three(a, b, c)
show m
show total
```

## Limitaciones actuales

- La deteccion de definiciones publicas es simple: solo `func` y `let`
  a nivel de bloque 0.
- No existe un sistema de namespaces; los simbolos importados comparten
  el mismo espacio global.
- Los includes de fuente se insertan una sola vez (include-once).

## Compatibilidad

El flujo anterior de `.import` y `.extern` para librerias compiladas se
mantiene intacto.
