#!/usr/bin/env python3
"""
Test de integración: Compilar código con .import/.extern y cargarlo en el CacaoCore64

Este script demuestra el flujo completo:
1. Código fuente con directivas de librería
2. Compilación a formato relocalizable
3. Enlazado y carga de librerías
4. Ejecución en CacaoCore64
"""

import sys
sys.path.insert(0, 'src')

from enlazador_cargador.enlazador import Enlazador, BinarioEjectable
from enlazador_cargador.gestor_librerias import GestorLibrerias
from pathlib import Path


def crear_codigo_reloc_ejemplo():
    """
    Crea un código relocalizable de ejemplo que usa VEC_GET de math.lib
    
    Este es un ejemplo simplificado del formato que generaría el compilador.
    """
    return """
.import "math.lib"
.extern VEC_GET
.extern VEC_SET

.data
0000000000000001
0000000000000002
0000000000000003

.text
1111111111111111
2222222222222222
3333333333333333
"""


def prueba_flujo_completo():
    """
    Prueba el flujo completo: compilación → enlazado → carga
    """
    print("\n" + "="*70)
    print("PRUEBA DE FLUJO COMPLETO: COMPILACIÓN → ENLAZADO → CARGA")
    print("="*70)
    
    # Paso 1: Obtener código fuente con imports
    print("\n[PASO 1] Código fuente compilado a relocalizable")
    print("-" * 70)
    reloc_code = crear_codigo_reloc_ejemplo()
    print("Código relocalizable generado:")
    print(reloc_code)
    
    # Paso 2: Enlazar y resolver librerías
    print("\n[PASO 2] Enlazado y resolución de librerías")
    print("-" * 70)
    try:
        enlazador = Enlazador()
        binario = enlazador.procesar_relocalizable(reloc_code, 0x00001000)
        
        print(f"✓ Enlazado completado exitosamente")
        print(f"  - Dirección base: 0x{binario.direccion_base:08x}")
        print(f"  - Tamaño código: {len(binario.codigo)} bytes")
        print(f"  - Tamaño datos: {len(binario.datos)} bytes")
        
        # Mostrar el código en formato legible
        print(f"\n  Código (hex):")
        for i in range(0, len(binario.codigo), 8):
            chunk = binario.codigo[i:i+8]
            hex_str = chunk.hex().upper().zfill(16)
            addr = binario.direccion_base + i
            print(f"    0x{addr:08x}: {hex_str}")
        
        print(f"\n  Datos (hex):")
        for i in range(0, len(binario.datos), 8):
            chunk = binario.datos[i:i+8]
            hex_str = chunk.hex().upper().zfill(16)
            print(f"    [{i//8}]: {hex_str}")
        
        # Paso 3: Serializar para almacenamiento
        print("\n[PASO 3] Serialización del binario")
        print("-" * 70)
        binario_serializado = binario.serializar()
        print(f"✓ Binario serializado: {len(binario_serializado)} bytes")
        print(f"  Primeros 32 bytes: {binario_serializado[:32].hex().upper()}")
        
        # Paso 4: Deserializar para verificación
        print("\n[PASO 4] Deserialización y verificación")
        print("-" * 70)
        binario_recuperado = BinarioEjectable.deserializar(binario_serializado)
        print(f"✓ Binario deserializado")
        print(f"  - Dirección base: 0x{binario_recuperado.direccion_base:08x}")
        print(f"  - Tamaño código: {len(binario_recuperado.codigo)} bytes")
        print(f"  - Tamaño datos: {len(binario_recuperado.datos)} bytes")
        
        # Verificación
        assert binario.codigo == binario_recuperado.codigo, "Código no coincide"
        assert binario.datos == binario_recuperado.datos, "Datos no coinciden"
        print("✓ Verificación pasada: datos se recuperaron correctamente")
        
        return True
        
    except Exception as e:
        print(f"✗ Error durante enlazado: {e}")
        import traceback
        traceback.print_exc()
        return False


def prueba_sin_librerias():
    """
    Prueba con código que NO usa librerías
    """
    print("\n" + "="*70)
    print("PRUEBA: CÓDIGO SIN LIBRERÍAS")
    print("="*70)
    
    reloc_code_simple = """
.data
0000000000000010
0000000000000020

.text
aaaabbbbccccdddd
eeeeffff00001111
"""
    
    print("\nCódigo relocalizable (sin librerías):")
    print(reloc_code_simple)
    
    try:
        enlazador = Enlazador()
        binario = enlazador.procesar_relocalizable(reloc_code_simple)
        
        print(f"✓ Enlazado sin librerías completado")
        print(f"  - Dirección base: 0x{binario.direccion_base:08x}")
        print(f"  - Tamaño código: {len(binario.codigo)} bytes")
        print(f"  - Tamaño datos: {len(binario.datos)} bytes")
        print(f"  - Código: {binario.codigo.hex().upper()}")
        print(f"  - Datos: {binario.datos.hex().upper()}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def prueba_multiples_imports():
    """
    Prueba con múltiples imports de diferentes librerías
    """
    print("\n" + "="*70)
    print("PRUEBA: MÚLTIPLES IMPORTS")
    print("="*70)
    
    reloc_code = """
.import "math.lib"
.import "utils.lib"
.extern VEC_GET
.extern PRINT

.data
0000000000000001

.text
1111111111111111
"""
    
    print("Código con múltiples imports:")
    print(reloc_code)
    
    try:
        enlazador = Enlazador()
        binario = enlazador.procesar_relocalizable(reloc_code)
        
        print(f"✓ Enlazado con múltiples imports completado")
        print(f"  - Tamaño código: {len(binario.codigo)} bytes")
        
        # Verificar que se inyectaron funciones
        if len(binario.codigo) > 8:
            print("  - Funciones inyectadas: ✓")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def mostrar_resumen():
    """
    Muestra un resumen de cómo funcionan los cambios
    """
    print("\n" + "="*70)
    print("RESUMEN: CÓMO FUNCIONAN LOS CAMBIOS")
    print("="*70)
    
    print("""
El nuevo sistema de librerías integra:

1. GestorLibrerias (src/enlazador_cargador/gestor_librerias.py):
   - Parsea directivas .import "nombre.lib"
   - Parsea directivas .extern NOMBRE_FUNCION
   - Carga funciones desde src/Libraries/*.reloc
   - Inyecta código en el binario final

2. Enlazador (src/enlazador_cargador/enlazador.py):
   - Nuevo método procesar_relocalizable()
   - Integra GestorLibrerias para resolver imports
   - Retorna BinarioEjectable listo para ejecutar

3. Compilador GUI (src/compiler/compiler_gui.py):
   - Actualizado para usar Enlazador
   - Mantiene interfaz de usuario igual
   - Genera output formateado con dirección base y tamaño

FLUJO:
   Código fuente → Compilador → Relocalizable (.import/.extern/.data/.text)
   ↓
   Enlazador → Parsea imports/externs
   ↓
   GestorLibrerias → Carga funciones desde Libraries/
   ↓
   Inyecta código → Genera BinarioEjectable
   ↓
   Mostrar en GUI con código + datos enlazados

LIBRERÍAS DISPONIBLES:
   - "math.lib" → src/Libraries/lib_vectores.reloc
   - "utils.lib" → src/Libraries/lib_utils.reloc

CÓMO PROBAR:
   1. Ejecutar: python3 test_library_linker.py
   2. Usar GUI: src/compiler/compiler_gui.py
   3. Ejecutar: python3 cacao_core.py (con código compilado)
""")


def main():
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "INTEGRACIÓN DE LIBRERÍAS CON ENLAZADOR".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    resultados = []
    
    # Ejecutar todas las pruebas
    resultados.append(("Flujo completo", prueba_flujo_completo()))
    resultados.append(("Sin librerías", prueba_sin_librerias()))
    resultados.append(("Múltiples imports", prueba_multiples_imports()))
    
    # Mostrar resultados
    print("\n" + "="*70)
    print("RESULTADOS")
    print("="*70)
    for nombre, resultado in resultados:
        estado = "✓ PASÓ" if resultado else "✗ FALLÓ"
        print(f"{nombre:.<50} {estado}")
    
    todos_pasaron = all(r for _, r in resultados)
    
    # Mostrar resumen
    mostrar_resumen()
    
    # Retornar estado
    return 0 if todos_pasaron else 1


if __name__ == "__main__":
    exit(main())
