# Flujo de importacion (preprocesador)

Este documento resume el flujo actual de importacion, diferenciando:
- Includes de librerias precompiladas
- Includes de archivos fuente (alto nivel)

## Caso A: include de libreria precompilada

Ejemplo:

```text
#include "utils.lib"
#include "math.lib" { VEC_MAX, VEC_SET }
```

Flujo:
1. El preprocesador detecta extensiones `.lib`, `.reloc` o `.obj` y trata el
   include como libreria compilada.
2. Emite `.import "<lib>"` en la salida.
3. Si hay lista `{ ... }`, emite `.extern` por cada simbolo.
4. En segunda pasada, reordena `.extern` debajo de su `.import`.
5. El linker procesa `.import` y `.extern` para cargar funciones desde
   `Libraries/*.reloc`.

Efecto en salida:

```text
.import "math.lib"
.extern VEC_MAX
.extern VEC_SET
```

## Caso B: include de otro archivo fuente

Ejemplo:

```text
#include "source_import_utils.txt" { max_of_three, total }
```

Flujo:
1. Si el include no termina en `.lib`/`.reloc`/`.obj`, se trata como fuente.
2. Se resuelve la ruta:
   - Relativa al archivo actual (si se conoce la ruta original).
   - Si no, busca recursivamente en `src/examples` y luego en `examples`.
3. El archivo incluido se preprocesa y su contenido se inserta en la salida.
4. Se valida la lista `{ ... }` contra los simbolos exportados del archivo.
5. Se detectan ciclos de importacion y conflictos de simbolos publicos.

## Export de simbolos

Se admite `#export` para declarar simbolos publicos de un archivo fuente:

```text
#export { max_of_three, total }

func max_of_three(a: int, b: int, c: int) { ... }
let total: int = 0
```

Reglas:
- Si hay `#export`, solo esos simbolos son publicos.
- Si no hay `#export`, se asume que todos los `func` y `let` de nivel superior
  son publicos por defecto.

## Auto-import por llamadas calificadas

Cuando hay llamadas calificadas de libreria, por ejemplo:

```text
math.lib.VEC_MAX(a, n)
```

El preprocesador detecta la funcion y agrega un `.extern VEC_MAX` debajo de
`.import "math.lib"`, sin necesidad de declarar la lista `{ ... }`.

## Integracion con la GUI

- Si cargas un archivo con "Load file", se usa su ruta real para resolver
  includes relativos.
- Si pegas texto directamente, se aplica la busqueda en `src/examples`.

## Resumen rapido

- Libreria compilada => `.import` + `.extern` (flujo original intacto).
- Archivo fuente => expansion en linea + `#export` para visibilidad.
- Se detectan ciclos y conflictos de simbolos.
