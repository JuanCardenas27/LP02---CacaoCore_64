#!/usr/bin/env python3
"""
Script de prueba del Enlazador-Cargador FLEX
=============================================
Demuestra el uso del nuevo gestor integrado.

Ejecutar desde src/:
    python3 test_enlazador_cargador.py
"""

import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enlazador_cargador.gestor_enlazador_cargador import GestorEnlazadorCargador
from enlazador_cargador.enlazador import BinarioEjectable

def test_1_carga_desde_archivos():
    """Test 1: Cargar desde archivos .obj"""
    print("\n" + "="*60)
    print("TEST 1: Carga desde archivos .obj")
    print("="*60)
    
    gestor = GestorEnlazadorCargador(verbose=True)
    
    rutas = [
        'ejemplos_modulos/modulo_main.obj',
        'ejemplos_modulos/modulo_biblioteca.obj'
    ]
    
    # Verificar que los archivos existen
    for ruta in rutas:
        if not os.path.exists(ruta):
            print(f"✗ Archivo no encontrado: {ruta}")
            return False
    
    exito = gestor.cargar_y_enlazar(rutas, direccion_base=0x00001000)
    
    if exito:
        print("\n✓ TEST 1 EXITOSO")
        tabla = gestor.obtener_tabla_simbolos()
        print(f"\nTabla de símbolos:")
        for nombre, simbolo in tabla.items():
            print(f"  {nombre}: {simbolo.tipo} @ 0x{simbolo.valor:X}")
        
        binario = gestor.obtener_ultimo_binario()
        print(f"\nBinario ejecutable:")
        print(f"  Dirección base: 0x{binario.direccion_base:08X}")
        print(f"  Código: {binario.codigo.hex()}")
        print(f"  Datos: {binario.datos.hex()}")
        return True
    else:
        print(f"\n✗ TEST 1 FALLÓ: {gestor.obtener_ultimo_error()}")
        return False


def test_2_carga_desde_contenido():
    """Test 2: Cargar desde contenido en memoria"""
    print("\n" + "="*60)
    print("TEST 2: Carga desde contenido en memoria")
    print("="*60)
    
    contenidos = {
        'modulo1': """
[MODULE modulo1]
[CODE] 48 89 C3 FF E0 00 00 00
[DATA] 00 01
[SYMBOLS] inicio:code:0x1000
[EXTERNAL]
        """,
        'modulo2': """
[MODULE modulo2]
[CODE] FF E0 00 00 00 00 00 00
[DATA] 02 03
[SYMBOLS] final:code:0x1003
[EXTERNAL] inicio:0x4:32bits
        """
    }
    
    gestor = GestorEnlazadorCargador(verbose=True)
    exito = gestor.cargar_desde_contenido(contenidos, cargar_en_memoria=False)
    
    if exito:
        print("\n✓ TEST 2 EXITOSO")
        binario = gestor.obtener_ultimo_binario()
        print(f"\nBinario resultante:")
        print(f"  Código: {binario.codigo.hex()}")
        print(f"  Datos: {binario.datos.hex()}")
        return True
    else:
        print(f"\n✗ TEST 2 FALLÓ: {gestor.obtener_ultimo_error()}")
        return False


def test_3_solo_enlazar():
    """Test 3: Solo enlazar sin cargar a memoria"""
    print("\n" + "="*60)
    print("TEST 3: Solo enlazar (sin cargar a memoria)")
    print("="*60)
    
    gestor = GestorEnlazadorCargador(verbose=True)
    
    rutas = [
        'ejemplos_modulos/modulo_main.obj',
        'ejemplos_modulos/modulo_biblioteca.obj'
    ]
    
    # No cargar en memoria
    exito = gestor.cargar_y_enlazar(rutas, cargar_en_memoria=False)
    
    if exito:
        print("\n✓ TEST 3 EXITOSO (Sin procesador involucrado)")
        binario = gestor.obtener_ultimo_binario()
        print(f"Binario enlazado sin cargar")
        return True
    else:
        print(f"\n✗ TEST 3 FALLÓ: {gestor.obtener_ultimo_error()}")
        return False


def test_4_serializar_binario():
    """Test 4: Serializar y deserializar binario"""
    print("\n" + "="*60)
    print("TEST 4: Serialización de binario")
    print("="*60)
    
    # Crear binario de prueba
    binario_orig = BinarioEjectable()
    binario_orig.direccion_base = 0x1000
    binario_orig.codigo = bytearray([0x48, 0x89, 0xC3])
    binario_orig.datos = bytearray([0x00, 0x01, 0x02])
    
    # Serializar
    datos_serializados = binario_orig.serializar()
    print(f"Serializado: {datos_serializados.hex()}")
    
    # Deserializar
    binario_nuevo = BinarioEjectable.deserializar(datos_serializados)
    
    # Verificar
    if (binario_nuevo.direccion_base == binario_orig.direccion_base and
        binario_nuevo.codigo == binario_orig.codigo and
        binario_nuevo.datos == binario_orig.datos):
        print("✓ TEST 4 EXITOSO (Serialización correcta)")
        return True
    else:
        print("✗ TEST 4 FALLÓ (Datos no coinciden)")
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n" + "="*60)
    print("PRUEBAS DEL ENLAZADOR-CARGADOR MEJORADO CON FLEX")
    print("="*60)
    
    # Cambiar a directorio src si es necesario
    if not os.path.exists('enlazador_cargador'):
        print("Debe ejecutar desde el directorio src/")
        return False
    
    resultados = [
        ("Carga desde archivos", test_1_carga_desde_archivos()),
        ("Carga desde contenido", test_2_carga_desde_contenido()),
        ("Solo enlazar", test_3_solo_enlazar()),
        ("Serialización", test_4_serializar_binario()),
    ]
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        estado = "✓ PASS" if resultado else "✗ FAIL"
        print(f"{estado}: {nombre}")
    
    print(f"\nTotal: {passed}/{total} pruebas exitosas")
    
    return passed == total


if __name__ == '__main__':
    exito = main()
    sys.exit(0 if exito else 1)
