"""
Gestor de Librerías para el Enlazador
======================================

Maneja .import y .extern directivas para resolver referencias a librerías.
Se integra con Enlazador para soportar el formato relocalizable
que viene del compilador con directivas .import "xxx.lib" y .extern función.
"""

import re
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class ErrorLibreria(Exception):
    """Error en manejo de librerías"""
    pass


class GestorLibrerias:
    """Gestiona carga y resolución de librerías"""

    # Mapeo de nombres de librería a archivos
    MAPEO_LIBRERIAS = {
        "math.lib": "lib_vectores.reloc",
        "utils.lib": "lib_utils.reloc",
    }

    # Regex para parsear directivas
    _RE_IMPORT = re.compile(r'^\s*\.import\s+"([^"]+)"', re.IGNORECASE)
    _RE_EXTERN = re.compile(r'^\s*\.extern\s+(\w+)', re.IGNORECASE)
    _RE_FUNC_DEF = re.compile(r'^@func\s+(\w+)\{(\d+)\}', re.IGNORECASE)

    def __init__(self, ruta_librerias: Optional[str] = None):
        """
        Inicializa el gestor de librerías.
        
        Args:
            ruta_librerias: Ruta a la carpeta Libraries. Si es None,
                          se asume ../Libraries relativo al módulo.
        """
        if ruta_librerias is None:
            # Ruta relativa al módulo actual
            ruta_base = Path(__file__).parent.parent
            self.ruta_librerias = ruta_base / "Libraries"
        else:
            self.ruta_librerias = Path(ruta_librerias)

        # Cache de librerías cargadas
        self._cache_librerias: Dict[str, Dict[str, bytearray]] = {}

    def parsear_directivas(self, reloc_text: str) -> Tuple[List[str], List[str]]:
        """
        Parsea un texto relocalizable y extrae .import y .extern directivas.
        
        Returns:
            Tupla (lista_imports, lista_externs)
            - lista_imports: ["math.lib", "utils.lib", ...]
            - lista_externs: ["VEC_GET", "VEC_SET", ...]
        """
        imports = []
        externs = []

        for linea in reloc_text.splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue

            # Buscar .import
            m = self._RE_IMPORT.match(linea)
            if m:
                imports.append(m.group(1))
                continue

            # Buscar .extern
            m = self._RE_EXTERN.match(linea)
            if m:
                externs.append(m.group(1))

        return imports, externs

    def cargar_libreria(self, lib_name: str) -> Dict[str, bytearray]:
        """
        Carga una librería y retorna mapa de funciones.
        
        Args:
            lib_name: Nombre de librería ("math.lib", "utils.lib", etc.)
            
        Returns:
            Dict: {nombre_funcion: codigo_hex_bytes}
            
        Raises:
            ErrorLibreria: Si no se encuentra o hay error al parsear
        """
        # Revisar cache
        if lib_name in self._cache_librerias:
            return self._cache_librerias[lib_name]

        # Mapear nombre a archivo
        if lib_name not in self.MAPEO_LIBRERIAS:
            raise ErrorLibreria(f"Librería desconocida: '{lib_name}'")

        nombre_archivo = self.MAPEO_LIBRERIAS[lib_name]
        ruta_archivo = self.ruta_librerias / nombre_archivo

        if not ruta_archivo.exists():
            raise ErrorLibreria(f"Archivo de librería no encontrado: {ruta_archivo}")

        # Leer archivo
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
        except OSError as e:
            raise ErrorLibreria(f"Error al leer librería {nombre_archivo}: {e}")

        # Parsear funciones
        funciones = self._parsear_libreria(contenido)

        # Guardar en cache
        self._cache_librerias[lib_name] = funciones

        return funciones

    def _parsear_libreria(self, contenido: str) -> Dict[str, bytearray]:
        """
        Parsea un archivo de librería y extrae funciones.
        
        Formato:
            .text
            @func NOMBRE{offset}
            PALABRA_HEX
            PALABRA_HEX
            ...
            @func OTRO{offset2}
            ...
        """
        funciones: Dict[str, bytearray] = {}
        lineas = contenido.splitlines()

        # Buscar la sección .text
        idx_text = -1
        for i, linea in enumerate(lineas):
            if linea.strip().lower() == '.text':
                idx_text = i + 1
                break

        if idx_text < 0:
            raise ErrorLibreria("Librería sin sección .text")

        # Parsear funciones en .text
        func_actual = None
        codigo_actual = bytearray()

        for linea in lineas[idx_text:]:
            linea = linea.strip()

            if not linea or linea.startswith("#"):
                continue

            # Detectar nueva función
            m = self._RE_FUNC_DEF.match(linea)
            if m:
                # Guardar función anterior si existe
                if func_actual:
                    funciones[func_actual] = codigo_actual

                func_actual = m.group(1)
                codigo_actual = bytearray()
                continue

            # Parsear línea de código hex (16 caracteres = 8 bytes)
            if func_actual and re.match(r'^[0-9a-fA-F]{16}$', linea):
                # Convertir hex a bytes (little-endian)
                try:
                    palabra = int(linea, 16)
                    codigo_actual.extend(palabra.to_bytes(8, byteorder='little'))
                except ValueError:
                    raise ErrorLibreria(f"Palabra hex inválida: {linea}")

        # Guardar última función
        if func_actual:
            funciones[func_actual] = codigo_actual

        return funciones

    def obtener_funciones(self, imports: List[str], externs: List[str]) -> Dict[str, bytearray]:
        """
        Obtiene todas las funciones externas requeridas.
        
        Args:
            imports: Lista de librerías a importar
            externs: Lista de funciones a extraer
            
        Returns:
            Dict: {nombre_funcion: codigo_bytes}
        """
        funciones_resueltas: Dict[str, bytearray] = {}

        for lib_name in imports:
            try:
                libreria = self.cargar_libreria(lib_name)
            except ErrorLibreria as e:
                raise ErrorLibreria(f"Error cargando {lib_name}: {e}")

            # Extraer solo las funciones solicitadas
            for func_name in externs:
                if func_name in libreria:
                    funciones_resueltas[func_name] = libreria[func_name]

        # Verificar que se encontraron todas las funciones
        funciones_faltantes = set(externs) - set(funciones_resueltas.keys())
        if funciones_faltantes:
            raise ErrorLibreria(
                f"Funciones no encontradas en librerías: {funciones_faltantes}"
            )

        return funciones_resueltas

    def inyectar_funciones(
        self,
        codigo: bytearray,
        funciones: Dict[str, bytearray]
    ) -> Dict[str, int]:
        """
        Inyecta código de funciones en el binario.
        
        Args:
            codigo: Bytearray con código existente
            funciones: Dict de {nombre: codigo_bytes}
            
        Returns:
            Dict: {nombre_funcion: offset_en_codigo}
        """
        mapa_offsets = {}

        for nombre, codigo_func in funciones.items():
            # Registrar offset antes de agregar
            mapa_offsets[nombre] = len(codigo)

            # Agregar código de función al final
            codigo.extend(codigo_func)

        return mapa_offsets

    def resolver_llamadas_externas(
        self,
        codigo: bytearray,
        texto_reloc: str,
        mapa_funciones: Dict[str, int]
    ) -> bytearray:
        """
        Resuelve llamadas a funciones externas (@func).
        
        Busca en el código referencias a "@func NombreFuncion" y
        reemplaza con la dirección real.
        
        Args:
            codigo: Código con referencias sin resolver
            texto_reloc: Texto relocalizable original
            mapa_funciones: Mapa de {nombre_funcion: offset}
            
        Returns:
            Código con referencias resueltas
        """
        # Este paso se hace típicamente durante la resolución
        # de referencias del enlazador general
        return codigo


__all__ = [
    'GestorLibrerias',
    'ErrorLibreria',
]
