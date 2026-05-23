#!/usr/bin/env python3
"""
GUÍA: CÓMO PROBAR EL NUEVO SISTEMA DE LIBRERÍAS
================================================

Este archivo explica cómo probar la integración de librerías con el enlazador.

CAMBIOS REALIZADOS:
===================

1. ARCHIVO NUEVO: src/enlazador_cargador/gestor_librerias.py
   - GestorLibrerias: clase que maneja .import y .extern
   - parsear_directivas(): extrae imports y externs del código
   - cargar_libreria(): carga un archivo .reloc desde src/Libraries/
   - obtener_funciones(): carga y cachea funciones solicitadas
   - inyectar_funciones(): agrega código de funciones al binario

2. MODIFICADO: src/enlazador_cargador/enlazador.py
   - Agregado: import de GestorLibrerias
   - Agregado: self.gestor_librerias en __init__
   - Nuevo método: procesar_relocalizable(reloc_text, direccion_base)
   - Nuevo método: _parsear_seccionnes_reloc(reloc_text)
   
   Estos métodos permiten procesar código relocalizable con .import y .extern

3. MODIFICADO: src/compiler/compiler_gui.py
   - Cambio de imports: ahora usa Enlazador en lugar de EnlazadorMejorado
   - Actualizado el método _ll_link() para usar procesar_relocalizable()
   - Agregado método: _formato_salida_binario() para mostrar el resultado

CÓMO PROBAR:
============

OPCIÓN 1: PRUEBAS AUTOMÁTICAS
------------------------------

Ejecuta los scripts de test:

  $ python3 test_library_linker.py
  
  Este script prueba:
  - Parsing de directivas .import y .extern
  - Carga de funciones desde librerías
  - Parsing de secciones .data y .text
  - Procesamiento completo con Enlazador
  - Inyección de funciones de librerías

  $ python3 test_integration.py
  
  Este script prueba:
  - Flujo completo: compilación → enlazado → serialización
  - Procesamiento sin librerías
  - Procesamiento con múltiples imports
  - Deserialización del binario

OPCIÓN 2: USAR LA GUI DEL COMPILADOR
-------------------------------------

1. Inicia la interfaz gráfica:
   $ python3 src/cacao_gui.py

2. Ve a la pestaña "Linker/Loader"

3. En la sección "Relocatable Format", ingresa código relocalizable como:

   .import "math.lib"
   .extern VEC_GET
   
   .data
   0000000000000001
   0000000000000002
   
   .text
   1234567890abcdef
   fedcba0987654321

4. Ingresa dirección base: 0000 (o 00001000 en hex)

5. Haz clic en "LINK" (el botón de enlazado)

6. Verás en la sección "Linked Code" el resultado:
   - Dirección base
   - Tamaño de código y datos
   - Código enlazado en hexadecimal
   - Datos en hexadecimal

OPCIÓN 3: CÓDIGO DE EJEMPLO PERSONALIZADO
------------------------------------------

Crea un archivo test_personalizado.py:

  import sys
  sys.path.insert(0, 'src')
  
  from enlazador_cargador.enlazador import Enlazador
  
  codigo = '''
  .import "math.lib"
  .extern VEC_GET
  
  .data
  0000000000000001
  
  .text
  1111111111111111
  '''
  
  enlazador = Enlazador()
  binario = enlazador.procesar_relocalizable(codigo)
  
  print(f"Código: {binario.codigo.hex().upper()}")
  print(f"Datos: {binario.datos.hex().upper()}")

Luego ejecuta:
  $ python3 test_personalizado.py

FORMATOS SOPORTADOS:
====================

CÓDIGO RELOCALIZABLE (entrada):
.import "nombre.lib"         # Cargar librería (una o más líneas)
.extern NOMBRE_FUNCION       # Función externa (una o más líneas)

.data                        # Sección de datos
hhhhhhhhhhhhhhhh            # Palabra hex (8 bytes en formato little-endian)
hhhhhhhhhhhhhhhh

.text                        # Sección de código
hhhhhhhhhhhhhhhh
hhhhhhhhhhhhhhhh

BINARIO EJECUTABLE (salida):
- Dirección base (8 bytes)
- Tamaño código (8 bytes)
- Código (N bytes)
- Tamaño datos (8 bytes)
- Datos (M bytes)

LIBRERÍAS DISPONIBLES:
======================

math.lib → src/Libraries/lib_vectores.reloc
Funciones:
  - VEC_GET
  - VEC_SET
  - Otras funciones de vectores

utils.lib → src/Libraries/lib_utils.reloc
Funciones:
  - PRINT
  - Otras funciones de utilidad

FORMATO DE LIBRERÍAS:
====================

Los archivos .reloc contienen:

@func NOMBRE_FUNCION{offset_en_palabras}
hhhhhhhhhhhhhhhh        # Palabra hex (8 bytes)
hhhhhhhhhhhhhhhh
...

Ejemplo de lib_vectores.reloc:

@func VEC_GET{0}
4230f0ffffffffff
...

@func VEC_SET{10}
...

CÓMO FUNCIONA:
==============

1. El compilador genera código relocalizable con .import y .extern
2. Enlazador.procesar_relocalizable() recibe este código
3. GestorLibrerias.parsear_directivas() extrae imports y externs
4. GestorLibrerias.obtener_funciones() carga funciones de las librerías
5. GestorLibrerias.inyectar_funciones() agrega el código al binario
6. Se retorna un BinarioEjectable listo para ejecutar

EJEMPLO DE SALIDA:
==================

Cuando ejecutas test_integration.py, ves algo como:

  [PASO 2] Enlazado y resolución de librerías
  ✓ Enlazado completado exitosamente
    - Dirección base: 0x00001000
    - Tamaño código: 104 bytes
    - Tamaño datos: 24 bytes
  
    Código (hex):
      0x00001000: 1111111111111111
      0x00001008: 2222222222222222
      0x00001010: 3333333333333333
      0x00001018: FFFFFFFFFFF03042  ← Función inyectada de librería
      ...

SOLUCIÓN DE PROBLEMAS:
======================

P: "Error: Función XXX no encontrada en librerías"
R: La función no existe en el archivo .reloc indicado.
   Verifica que el nombre sea correcto y que esté en la librería.

P: "No funciona la GUI"
R: Asegúrate de que estés en la carpeta del proyecto y ejecutes:
   python3 src/cacao_gui.py

P: "El código no se enlaza"
R: Verifica que:
   - El formato sea correcto (palabras de 16 hex chars)
   - Haya secciones .data y .text
   - Los nombres de librerías sean "math.lib" o "utils.lib"

PRÓXIMOS PASOS:
===============

- Usar el nuevo sistema en el compilador de alto nivel
- Generar ejemplos con código completo en CacaoCore
- Validar que las referencias a funciones se resuelvan correctamente
- Probar ejecución en el simulador

"""

# Script de demostración simple
if __name__ == "__main__":
    print(__doc__)
    
    print("\n" + "="*70)
    print("EJECUTANDO DEMOSTRACIÓN RÁPIDA")
    print("="*70)
    
    import sys
    sys.path.insert(0, 'src')
    
    from enlazador_cargador.enlazador import Enlazador
    
    # Código simple sin librerías
    codigo_simple = """
    .data
    0000000000000010
    
    .text
    aaaaaaaaaaaaaaaa
    """
    
    print("\nCódigo simple:")
    print(codigo_simple)
    
    try:
        enlazador = Enlazador()
        binario = enlazador.procesar_relocalizable(codigo_simple)
        
        print("\nResultado:")
        print(f"  Dirección base: 0x{binario.direccion_base:08x}")
        print(f"  Tamaño código: {len(binario.codigo)} bytes")
        print(f"  Tamaño datos: {len(binario.datos)} bytes")
        print(f"  Código: {binario.codigo.hex().upper()}")
        print(f"  Datos: {binario.datos.hex().upper()}")
        print("\n✓ ¡El nuevo sistema funciona!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
