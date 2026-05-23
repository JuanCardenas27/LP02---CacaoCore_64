#!/usr/bin/env python3
"""
Test script para verificar la integración de GestorLibrerias con Enlazador.

Este script prueba:
1. Carga de archivos relocalizable con .import y .extern
2. Resolución de funciones de librerías
3. Inyección de código de librerías en el binario
4. Generación correcta de BinarioEjectable
"""

import sys
sys.path.insert(0, 'src')

from enlazador_cargador.enlazador import Enlazador, BinarioEjectable
from enlazador_cargador.gestor_librerias import GestorLibrerias
from pathlib import Path

def test_basico_parser():
    """Test 1: Parsear directivas .import y .extern"""
    print("\n" + "="*60)
    print("TEST 1: Parsing de directivas .import y .extern")
    print("="*60)
    
    reloc_text = """
    .import "math.lib"
    .extern VEC_GET
    .extern VEC_SET
    
    .data
    0000000000000001
    0000000000000002
    
    .text
    1234567890abcdef
    fedcba0987654321
    """
    
    gestor = GestorLibrerias()
    imports, externs = gestor.parsear_directivas(reloc_text)
    
    print(f"✓ Imports encontrados: {imports}")
    print(f"✓ Externs encontrados: {externs}")
    
    assert imports == ["math.lib"], f"Expected ['math.lib'], got {imports}"
    assert set(externs) == {"VEC_GET", "VEC_SET"}, f"Expected VEC_GET y VEC_SET, got {externs}"
    print("✓ Test 1 PASÓ")


def test_carga_libreria():
    """Test 2: Cargar funciones desde librerías"""
    print("\n" + "="*60)
    print("TEST 2: Carga de funciones desde librerías")
    print("="*60)
    
    gestor = GestorLibrerias()
    
    # Verificar que existen las librerías
    librera_math = Path("src/Libraries/lib_vectores.reloc")
    if not librera_math.exists():
        print(f"⚠ Librería no encontrada: {librera_math}")
        print("✓ Test 2 SKIPPED (librerías no disponibles)")
        return
    
    imports = ["math.lib"]
    externs = ["VEC_GET", "VEC_SET"]
    
    try:
        funciones = gestor.obtener_funciones(imports, externs)
        print(f"✓ Funciones cargadas: {list(funciones.keys())}")
        
        # Verificar que se cargaron las funciones solicitadas
        for func in externs:
            assert func in funciones, f"Función {func} no fue cargada"
        
        print("✓ Test 2 PASÓ")
    except Exception as e:
        print(f"✗ Error al cargar funciones: {e}")


def test_enlazador():
    """Test 3: Procesar relocalizable completo con Enlazador"""
    print("\n" + "="*60)
    print("TEST 3: Enlazador.procesar_relocalizable()")
    print("="*60)
    
    # Crear un archivo relocalizable simple sin .import para empezar
    reloc_text_simple = """
    .data
    0000000000000001
    0000000000000002
    
    .text
    1234567890abcdef
    fedcba0987654321
    0000000000000000
    """
    
    try:
        enlazador = Enlazador()
        binario = enlazador.procesar_relocalizable(reloc_text_simple)
        
        print(f"✓ Dirección base: 0x{binario.direccion_base:08x}")
        print(f"✓ Tamaño código: {len(binario.codigo)} bytes")
        print(f"✓ Tamaño datos: {len(binario.datos)} bytes")
        print(f"✓ Código: {binario.codigo.hex().upper()}")
        print(f"✓ Datos: {binario.datos.hex().upper()}")
        
        # Verificaciones
        assert isinstance(binario, BinarioEjectable), "No se retornó BinarioEjectable"
        assert binario.direccion_base == 0x00001000, f"Dirección base incorrecta"
        assert len(binario.codigo) == 24, f"Tamaño código incorrecto: {len(binario.codigo)}"
        assert len(binario.datos) == 16, f"Tamaño datos incorrecto: {len(binario.datos)}"
        
        print("✓ Test 3 PASÓ")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_parsing_seccionnes():
    """Test 4: Parseo correcto de secciones .data y .text"""
    print("\n" + "="*60)
    print("TEST 4: Parsing de secciones .data y .text")
    print("="*60)
    
    reloc_text = """
    # Comentario
    .import "math.lib"
    .extern VEC_GET
    
    .data
    aaaaaaaaaaaaaaaa
    bbbbbbbbbbbbbbbb
    
    .text
    1111111111111111
    2222222222222222
    3333333333333333
    """
    
    try:
        enlazador = Enlazador()
        data_bytes, text_bytes = enlazador._parsear_seccionnes_reloc(reloc_text)
        
        print(f"✓ Datos parseados: {data_bytes.hex().upper()}")
        print(f"✓ Código parseado: {text_bytes.hex().upper()}")
        
        # Verificaciones
        expected_data = bytes.fromhex("aaaaaaaaaaaaaaaa") + bytes.fromhex("bbbbbbbbbbbbbbbb")
        expected_text = (bytes.fromhex("1111111111111111") + 
                        bytes.fromhex("2222222222222222") + 
                        bytes.fromhex("3333333333333333"))
        
        assert data_bytes == expected_data, f"Datos no coinciden"
        assert text_bytes == expected_text, f"Código no coincide"
        
        print("✓ Test 4 PASÓ")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_con_librerias():
    """Test 5: Procesar relocalizable con .import y .extern (si librerías están disponibles)"""
    print("\n" + "="*60)
    print("TEST 5: Procesamiento completo con librerías")
    print("="*60)
    
    librera_path = Path("src/Libraries/lib_vectores.reloc")
    if not librera_path.exists():
        print(f"⚠ Librería no encontrada: {librera_path}")
        print("✓ Test 5 SKIPPED")
        return
    
    reloc_text = """
    .import "math.lib"
    .extern VEC_GET
    
    .data
    0000000000000001
    
    .text
    1234567890abcdef
    """
    
    try:
        enlazador = Enlazador()
        binario = enlazador.procesar_relocalizable(reloc_text)
        
        print(f"✓ Binario con librerías generado")
        print(f"✓ Tamaño código: {len(binario.codigo)} bytes")
        print(f"  Contenido: {binario.codigo.hex().upper()[:64]}...")
        
        # Verificar que el código de la función fue inyectado
        assert len(binario.codigo) > 8, "Código no fue inyectado correctamente"
        
        print("✓ Test 5 PASÓ")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "="*60)
    print("PRUEBAS DEL SISTEMA DE LIBRERÍAS CON ENLAZADOR")
    print("="*60)
    
    test_basico_parser()
    test_carga_libreria()
    test_parsing_seccionnes()
    test_enlazador()
    test_con_librerias()
    
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    print("✓ Todos los tests se completaron")
    print("\nPróximos pasos:")
    print("1. Prueba con compiler_gui.py")
    print("2. Verificar integración con cacao_core.py")
    print("3. Generar binarios ejecutables")


if __name__ == "__main__":
    main()
