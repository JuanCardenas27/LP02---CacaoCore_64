"""
Enlazador Mejorado con PLY
==========================
Resuelve referencias externas entre múltiples módulos objeto.

Basado en enlazador.py original pero integrado con analizador_modulos.py
"""

import struct
import re
from typing import Dict, List
from compiler.analizador_modulos import AnalizadorModulos, Simbolo
from .gestor_librerias import GestorLibrerias, ErrorLibreria


class ErrorEnlazador(Exception):
    """Excepción base para errores del enlazador"""
    pass


class SimboloNoDefinido(ErrorEnlazador):
    """Se referencia un símbolo no definido en ningún módulo"""
    pass


class SimboloDuplicado(ErrorEnlazador):
    """Un símbolo está definido en múltiples módulos"""
    pass


class ErrorValidacionBinario(ErrorEnlazador):
    """Error en la validación del binario ejecutable"""
    pass


class BinarioEjectable:
    """Formato de binario ejecutable después del enlazado"""

    def __init__(self):
        self.direccion_base = 0
        self.codigo = bytearray()
        self.datos = bytearray()

    def serializar(self) -> bytes:
        """Serializa el binario a formato compacto"""
        resultado = bytearray()
        resultado.extend(struct.pack("<Q", self.direccion_base))
        resultado.extend(struct.pack("<Q", len(self.codigo)))
        resultado.extend(self.codigo)
        resultado.extend(struct.pack("<Q", len(self.datos)))
        resultado.extend(self.datos)
        return bytes(resultado)

    @staticmethod
    def deserializar(datos: bytes) -> 'BinarioEjectable':
        """Deserializa un binario desde formato compacto"""
        if len(datos) < 24:
            raise ErrorValidacionBinario("Binario demasiado pequeño")

        binario = BinarioEjectable()
        offset = 0

        binario.direccion_base = struct.unpack_from("<Q", datos, offset)[0]
        offset += 8

        tam_codigo = struct.unpack_from("<Q", datos, offset)[0]
        offset += 8

        binario.codigo = bytearray(datos[offset:offset + tam_codigo])
        offset += tam_codigo

        tam_datos = struct.unpack_from("<Q", datos, offset)[0]
        offset += 8

        if offset + tam_datos != len(datos):
            raise ErrorValidacionBinario("Tamaño de datos inválido")

        binario.datos = bytearray(datos[offset:offset + tam_datos])

        return binario


class Modulo:
    """Representa un módulo objeto cargado"""

    def __init__(self, nombre: str):
        self.nombre = nombre
        self.codigo = bytearray()
        self.datos = bytearray()
        self.simbolos_definidos: Dict[str, Simbolo] = {}
        self.referencias_externas: Dict[str, List[tuple]] = {}


class Enlazador:
    """Enlazador que integra análisis léxico con PLY y manejo de librerías"""

    def __init__(self):
        self.modulos: List[Modulo] = []
        self.tabla_simbolos_global: Dict[str, Simbolo] = {}
        self.codigo_enlazado = bytearray()
        self.datos_enlazados = bytearray()
        self.mapeo_direcciones: Dict[str, int] = {}
        self.analizador = AnalizadorModulos()
        self.gestor_librerias = GestorLibrerias()
        self.mapa_funciones: Dict[str, int] = {}  # nombre_funcion -> offset

    def procesar_relocalizable(self, reloc_text: str, direccion_base: int = 0x00001000) -> BinarioEjectable:
        """
        Procesa código relocalizable con .import y .extern directivas.
        
        Este es el nuevo método que reemplaza la funcionalidad de linker.py
        pero dentro del sistema de Enlazador.
        
        Args:
            reloc_text: Texto con formato relocalizable (.import, .extern, .data, .text)
            direccion_base: Dirección base para cargar el código
            
        Returns:
            BinarioEjectable listo para ejecutar
            
        Raises:
            ErrorEnlazador: Si hay errores en el procesamiento
        """
        try:
            # Paso 1: Parsear directivas .import y .extern
            imports, externs = self.gestor_librerias.parsear_directivas(reloc_text)

            # Paso 2: Cargar funciones de librerías si hay imports
            funciones_cargadas = {}
            if imports and externs:
                funciones_cargadas = self.gestor_librerias.obtener_funciones(imports, externs)

            # Paso 3: Parsear secciones .data y .text
            data_bytes, text_bytes = self._parsear_seccionnes_reloc(reloc_text)

            # Paso 4: Inyectar funciones en el código
            codigo_final = bytearray(text_bytes)
            if funciones_cargadas:
                self.mapa_funciones = self.gestor_librerias.inyectar_funciones(
                    codigo_final, 
                    funciones_cargadas
                )

            # Paso 5: Construir binario ejecutable
            binario = BinarioEjectable()
            binario.direccion_base = direccion_base
            binario.codigo = codigo_final
            binario.datos = bytearray(data_bytes)

            return binario

        except ErrorLibreria as e:
            raise ErrorEnlazador(f"Error al cargar librerías: {e}")
        except Exception as e:
            raise ErrorEnlazador(f"Error procesando relocalizable: {e}")

    def _parsear_seccionnes_reloc(self, reloc_text: str) -> tuple:
        """
        Parsea las secciones .data y .text de un formato relocalizable.
        
        Returns:
            Tupla (data_bytes, text_bytes)
        """
        data_words = []
        text_words = []
        seccion_actual = None

        for linea in reloc_text.splitlines():
            linea = linea.strip()

            # Ignorar líneas vacías y comentarios
            if not linea or linea.startswith("#"):
                continue

            # Ignorar directivas de import/extern
            if linea.lower().startswith(".import") or linea.lower().startswith(".extern"):
                continue

            # Detectar secciones
            if linea.lower() == ".data":
                seccion_actual = "data"
                continue
            elif linea.lower() == ".text":
                seccion_actual = "text"
                continue

            # Procesar según sección
            if seccion_actual == "data":
                # Validar que sea palabra hex válida (16 nibbles)
                if re.match(r"^[0-9a-fA-F]{16}$", linea):
                    data_words.append(linea)

            elif seccion_actual == "text":
                # Validar palabra hex
                if re.match(r"^[0-9a-fA-F]{16}$", linea):
                    text_words.append(linea)

        # Convertir palabras hex a bytes
        data_bytes = bytearray()
        for word in data_words:
            valor = int(word, 16)
            data_bytes.extend(valor.to_bytes(8, byteorder='little'))

        text_bytes = bytearray()
        for word in text_words:
            valor = int(word, 16)
            text_bytes.extend(valor.to_bytes(8, byteorder='little'))

        return data_bytes, text_bytes

    def agregar_archivo_modulo(self, contenido: str) -> None:
        """
        Analiza un archivo de módulo (texto) y lo agrega al enlazador.
        
        Args:
            contenido: Texto del archivo del módulo en formato [MODULE] [CODE] etc.
        """
        try:
            # Analiza el módulo usando PLY
            info_modulo = self.analizador.parse_module(contenido)

            if not info_modulo['nombre']:
                raise ErrorEnlazador("Módulo sin nombre especificado")

            # Crea objeto Modulo
            modulo = Modulo(info_modulo['nombre'])
            modulo.codigo = info_modulo['codigo']
            modulo.datos = info_modulo['datos']
            modulo.simbolos_definidos = info_modulo['simbolos']
            modulo.referencias_externas = info_modulo['referencias_externas']

            self.modulos.append(modulo)

        except Exception as e:
            raise ErrorEnlazador(f"Error al procesar módulo: {e}")

    def enlazar(self, direccion_base: int = 0x00001000) -> BinarioEjectable:
        """
        Enlaza todos los módulos agregados.
        
        Args:
            direccion_base: Dirección base donde cargar el código
            
        Returns:
            BinarioEjectable listo para cargar
        """
        self._verificar_modulos()
        self._construir_tabla_simbolos_global()
        self._resolver_referencias()
        self._unificar_segmentos()

        binario = BinarioEjectable()
        binario.direccion_base = direccion_base
        binario.codigo = self.codigo_enlazado
        binario.datos = self.datos_enlazados

        return binario

    def _verificar_modulos(self) -> None:
        """Verifica que haya módulos para enlazar"""
        if not self.modulos:
            raise ErrorEnlazador("No hay módulos para enlazar")

    def _construir_tabla_simbolos_global(self) -> None:
        """Construye tabla de símbolos global verificando duplicados"""
        for modulo in self.modulos:
            for nombre, simbolo in modulo.simbolos_definidos.items():
                if nombre in self.tabla_simbolos_global:
                    raise SimboloDuplicado(
                        f"Símbolo '{nombre}' definido en "
                        f"'{modulo.nombre}' y "
                        f"'{self.tabla_simbolos_global[nombre]}'"
                    )
                self.tabla_simbolos_global[nombre] = simbolo

    def _resolver_referencias(self) -> None:
        """
        Resuelve referencias externas entre módulos.
        Modifica el código de cada módulo reemplazando referencias.
        """
        for modulo in self.modulos:
            for simbolo_externo, referencias in modulo.referencias_externas.items():
                if simbolo_externo not in self.tabla_simbolos_global:
                    raise SimboloNoDefinido(
                        f"Símbolo '{simbolo_externo}' referenciado en "
                        f"'{modulo.nombre}' pero no definido"
                    )

                direccion_resuelta = self.tabla_simbolos_global[simbolo_externo].valor

                # Resuelve cada referencia (puede ser objeto ReferenciaExterna o tupla)
                for referencia in referencias:
                    # Maneja tanto ReferenciaExterna como tuplas
                    if hasattr(referencia, 'posicion'):
                        posicion = referencia.posicion
                        tipo_operando = referencia.tipo
                    else:
                        posicion, tipo_operando = referencia
                    
                    if tipo_operando == "32bits":
                        struct.pack_into(
                            "<I", modulo.codigo, posicion,
                            direccion_resuelta & 0xFFFFFFFF
                        )
                    elif tipo_operando == "16bits":
                        struct.pack_into(
                            "<H", modulo.codigo, posicion,
                            direccion_resuelta & 0xFFFF
                        )
                    elif tipo_operando == "8bits":
                        struct.pack_into(
                            "<B", modulo.codigo, posicion,
                            direccion_resuelta & 0xFF
                        )
                    else:
                        raise ErrorEnlazador(
                            f"Tipo de operando desconocido: {tipo_operando}"
                        )

    def _unificar_segmentos(self) -> None:
        """Unifica código y datos de todos los módulos"""
        self.codigo_enlazado = bytearray()
        self.datos_enlazados = bytearray()

        for modulo in self.modulos:
            self.codigo_enlazado.extend(modulo.codigo)
            self.datos_enlazados.extend(modulo.datos)

    def obtener_tabla_simbolos(self) -> Dict[str, Simbolo]:
        """Retorna la tabla de símbolos global construida"""
        return self.tabla_simbolos_global.copy()

    def limpiar(self) -> None:
        """Limpia el estado del enlazador para nuevo proceso"""
        self.modulos.clear()
        self.tabla_simbolos_global.clear()
        self.codigo_enlazado = bytearray()
        self.datos_enlazados = bytearray()
        self.mapeo_direcciones.clear()


# Instancia global del enlazador
enlazador = Enlazador()
