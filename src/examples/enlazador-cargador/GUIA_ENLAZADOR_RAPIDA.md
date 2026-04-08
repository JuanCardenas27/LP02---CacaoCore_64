# Enlazador-Cargador FLEX - Guía de Uso

## 📌 Resumen Rápido

El **Enlazador-Cargador Mejorado** con FLEX (PLY) reemplaza el antiguo `loader/cacao_loader.py` con un sistema profesional que:

✅ Analiza módulos objeto (.obj) con lexer FLEX
✅ Enlaza múltiples módulos resolviendo símbolos
✅ Carga binarios en memoria con validación completa
✅ Se integra automáticamente con `cacao_gui.py`

---

## 🚀 Inicio Rápido

### 1. Instalación de Dependencias

```bash
pip install ply
```

### 2. Uso Básico en Python

```python
from src.enlazador_cargador.gestor_enlazador_cargador import GestorEnlazadorCargador
from src.cacao_core import CacaoCore64

# Crear procesador
core = CacaoCore64()

# Crear gestor
gestor = GestorEnlazadorCargador(procesador=core, verbose=True)

# Cargar módulos
rutas = ['modulo1.obj', 'modulo2.obj']
if gestor.cargar_y_enlazar(rutas):
    print("✓ Carga exitosa")
else:
    print(f"✗ Error: {gestor.obtener_ultimo_error()}")
```

---

## 📁 Estructura de Módulos Objeto

Crear archivos `.obj` con este formato:

```
[MODULE nombre_modulo]
[CODE] 48 89 C3 FF E0 90
[DATA] 00 01 02 03
[SYMBOLS] funcion1:code:0x1000,var1:data:0x2000
[EXTERNAL] funcion_externa:0x4:32bits
```

### Componentes:
- **[MODULE]**: Identificador único del módulo
- **[CODE]**: Instrucciones en hexadecimal
- **[DATA]**: Datos iniciales
- **[SYMBOLS]**: `nombre:tipo:valor`
- **[EXTERNAL]**: Referencias `nombre:posicion:tipo_operando`

---

## 💻 API Principal

### GestorEnlazadorCargador

```python
gestor = GestorEnlazadorCargador(procesador=None, verbose=False)
```

#### Métodos:

| Método | Descripción | Retorna |
|--------|-------------|---------|
| `cargar_y_enlazar(rutas, dir_base, cargar)` | Carga, enlaza y opcionalmente carga a memoria | bool |
| `cargar_desde_contenido(contenidos, dir_base, cargar)` | Idem pero desde strings | bool |
| `obtener_ultimo_error()` | Retorna error si falla | str |
| `obtener_ultimo_binario()` | Retorna binario enlazado | BinarioEjectable |
| `obtener_tabla_simbolos()` | Retorna tabla de símbolos | dict |

---

## 📝 Ejemplos

### Ejemplo 1: Dos módulos con referencias

**modulo1.obj:**
```
[MODULE principal]
[CODE] 48 89 C3 00 00 00 00 00
[DATA] 00 01
[SYMBOLS] inicio:code:0x1000
[EXTERNAL] inicializar:0x4:32bits
```

**modulo2.obj:**
```
[MODULE libreria]
[CODE] 90 90 90 C3
[DATA] 02 03
[SYMBOLS] inicializar:function:0x2000
[EXTERNAL]
```

**Script:**
```python
gestor = GestorEnlazadorCargador(verbose=True)
gestor.cargar_y_enlazar(['modulo1.obj', 'modulo2.obj'])

tabla = gestor.obtener_tabla_simbolos()
print(tabla)
# Output:
# {
#   'inicio': Simbolo(nombre='inicio', tipo='code', valor=0x1000),
#   'inicializar': Simbolo(nombre='inicializar', tipo='function', valor=0x2000)
# }
```

### Ejemplo 2: Solo enlazar (sin cargar a RAM)

```python
gestor = GestorEnlazadorCargador()

# No cargar en memoria
if gestor.cargar_y_enlazar(['m1.obj', 'm2.obj'], cargar_en_memoria=False):
    binario = gestor.obtener_ultimo_binario()
    
    # Guardar binario enlazado
    with open('programa.bin', 'wb') as f:
        f.write(binario.serializar())
```

### Ejemplo 3: Uso sin archivos

```python
contenidos = {
    'modulo1': '[MODULE m1]\n[CODE] 48 89 C3\n[DATA]\n[SYMBOLS] f:code:0x1000\n[EXTERNAL]',
    'modulo2': '[MODULE m2]\n[CODE] 90 90\n[DATA]\n[SYMBOLS]\n[EXTERNAL] f:0x0:32bits'
}

gestor = GestorEnlazadorCargador()
gestor.cargar_desde_contenido(contenidos)
```

---

## 🔧 Componentes Internos

```
src/
├── compiler/
│   └── analizador_modulos.py       ← Análisis léxico de módulos
├── enlazador_cargador/
│   ├── enlazador_mejorado.py       ← Resolución de símbolos
│   ├── cargador_mejorado.py        ← Carga a memoria
│   └── gestor_enlazador_cargador.py ← Interfaz principal
└── test_enlazador_cargador.py      ← Suite de tests
```

### Clases

**AnalizadorModulos** - Análisis léxico con PLY
```python
analizador = AnalizadorModulos()
info = analizador.parse_module(contenido)
# Retorna: {nombre, codigo, datos, simbolos, referencias_externas}
```

**EnlazadorMejorado** - Resolución de símbolos
```python
enlazador = EnlazadorMejorado()
enlazador.agregar_archivo_modulo(contenido)
binario = enlazador.enlazar(0x1000)
```

**CargadorMejorado** - Carga en memoria
```python
cargador = CargadorMejorado(procesador=core)
cargador.cargar(binario, verbose=True)
```

---

## ⚠️ Manejo de Errores

```python
gestor = GestorEnlazadorCargador()

if not gestor.cargar_y_enlazar(rutas):
    error = gestor.obtener_ultimo_error()
    
    # Errores comunes:
    # - "Archivo no encontrado: X"
    # - "Error en enlazador: Símbolo 'X' no definido"
    # - "Error en cargador: Dirección base fuera de rango"
    # - "Error al copiar a RAM: X"
```

---

## ✅ Validaciones Automáticas

El sistema valida:
- ✓ Archivos existen y son legibles
- ✓ Módulos tienen nombre único
- ✓ Código cabe en memoria de código (CODE_START a CODE_END)
- ✓ Datos caben en memoria de datos (DATA_START a DATA_END)
- ✓ Dirección base >= 0x1000 (no invade zona de sistema)
- ✓ Símbolos no duplicados entre módulos
- ✓ Todas las referencias externas están definidas

---

## 🧪 Pruebas

Ejecutar suite de tests:

```bash
cd src
python3 test_enlazador_cargador.py
```

Salida esperada:
```
============================================================
RESUMEN DE PRUEBAS
============================================================
✓ PASS: Carga desde archivos
✓ PASS: Carga desde contenido
✓ PASS: Solo enlazar
✓ PASS: Serialización

Total: 4/4 pruebas exitosas
```

---

## 📋 Diferencias: Antiguo vs Nuevo

| Característica | Antiguo loader | Nuevo enlazador |
|---|---|---|
| Análisis | Manual texto | FLEX (PLY) |
| Módulos | No | Múltiples |
| Símbolos | No | Tabla global |
| Referencias | No | Resolución automática |
| Validación | Mínima | Completa |
| Formato | .txt | .obj estructurado |
| Error handling | Básico | Detallado |

---

## 📖 Integración con GUI

El archivo `cacao_gui.py` ha sido actualizado automáticamente:

```python
# Antes
from loader.cacao_loader import loader

# Ahora
from enlazador_cargador.gestor_enlazador_cargador import GestorEnlazadorCargador
```

**La GUI sigue funcionando igual**, pero internamente usa el nuevo sistema.

---

## 🎯 Notas Importantes

1. **Dirección base**: Debe ser >= 0x1000
2. **Formato hexadecimal**: Use `0x` para valores hex, sin prefijo para decimales
3. **Orden de módulos**: Define primero modulos que dependen (sí importa)
4. **Verbose**: Activa con `verbose=True` para depuración

---

## 🚀 Próximas Mejoras

- [ ] Tablas de reubicación dinámicas
- [ ] Símbolos débiles
- [ ] Mapas de símbolos (.map)
- [ ] Bibliotecas precompiladas
- [ ] Linker scripts

---

**Última actualización**: 2026-04-06 | **Estado**: ✅ Production Ready
