"""
Gestor Unificado del Enlazador-Cargador
========================================
API simple e integrada para enlazar y cargar módulos objeto.

Uso típico:
    gestor = GestorEnlazadorCargador(procesador)
    exito = gestor.cargar_y_enlazar(['modulo1.obj', 'modulo2.obj'], 0x1000)
    if exito:
        print("Carga exitosa")
    else:
        print(gestor.obtener_ultimo_error())
"""

import os
from typing import List, Optional, Dict
from .enlazador import EnlazadorMejorado, BinarioEjectable, ErrorEnlazador
from .cargador import CargadorMejorado, ErrorCargador


class GestorEnlazadorCargador:
    """Gestor unificado que coordina enlazado y cargado de módulos"""

    def __init__(self, procesador=None, verbose: bool = False):
        """
        Inicializa el gestor.
        
        Args:
            procesador: Instancia del procesador (opcional)
            verbose: Si True, imprime información detallada
        """
        self.procesador = procesador
        self.verbose = verbose
        self.enlazador = EnlazadorMejorado()
        self.cargador = CargadorMejorado(procesador)
        self.ultimo_error = None
        self.ultimo_binario: Optional[BinarioEjectable] = None

    def cargar_y_enlazar(
        self,
        rutas_modulos: List[str],
        direccion_base: int = 0x00001000,
        cargar_en_memoria: bool = True
    ) -> bool:
        """
        Carga, enlaza y opcionalmente carga en memoria múltiples módulos.
        
        Args:
            rutas_modulos: Lista de rutas a archivos .obj
            direccion_base: Dirección base para cargar el código
            cargar_en_memoria: Si False, solo enlaza sin cargar a RAM
            
        Returns:
            True si todo fue exitoso, False si hay error
        """
        try:
            self.ultimo_error = None
            self.enlazador.limpiar()

            if self.verbose:
                print(f"[GESTOR] Procesando {len(rutas_modulos)} módulo(s)...")

            # Carga cada módulo
            for ruta in rutas_modulos:
                if not os.path.exists(ruta):
                    self.ultimo_error = f"Archivo no encontrado: {ruta}"
                    if self.verbose:
                        print(f"✗ {self.ultimo_error}")
                    return False

                try:
                    with open(ruta, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                except Exception as e:
                    self.ultimo_error = f"Error al leer {ruta}: {e}"
                    if self.verbose:
                        print(f"✗ {self.ultimo_error}")
                    return False

                try:
                    self.enlazador.agregar_archivo_modulo(contenido)
                    if self.verbose:
                        print(f"✓ Módulo cargado: {ruta}")
                except ErrorEnlazador as e:
                    self.ultimo_error = f"Error al procesar {ruta}: {e}"
                    if self.verbose:
                        print(f"✗ {self.ultimo_error}")
                    return False

            # Enlaza los módulos
            try:
                if self.verbose:
                    print(f"[GESTOR] Enlazando módulos...")
                self.ultimo_binario = self.enlazador.enlazar(direccion_base)
                if self.verbose:
                    print(f"✓ Enlazado exitoso")
            except ErrorEnlazador as e:
                self.ultimo_error = f"Error en enlazador: {e}"
                if self.verbose:
                    print(f"✗ {self.ultimo_error}")
                return False

            # Carga en memoria si se solicita
            if cargar_en_memoria:
                try:
                    if self.verbose:
                        print(f"[GESTOR] Cargando en memoria...")
                    exito = self.cargador.cargar(self.ultimo_binario, verbose=self.verbose)
                    if not exito:
                        self.ultimo_error = "Error al cargar en memoria"
                        return False
                    if self.verbose:
                        print(f"✓ Cargado en memoria exitosamente")
                except ErrorCargador as e:
                    self.ultimo_error = f"Error en cargador: {e}"
                    if self.verbose:
                        print(f"✗ {self.ultimo_error}")
                    return False

            if self.verbose:
                print(f"[GESTOR] Proceso completado exitosamente")

            return True

        except Exception as e:
            self.ultimo_error = f"Error inesperado: {e}"
            if self.verbose:
                print(f"✗ {self.ultimo_error}")
            return False

    def cargar_desde_contenido(
        self,
        contenidos: Dict[str, str],
        direccion_base: int = 0x00001000,
        cargar_en_memoria: bool = True
    ) -> bool:
        """
        Enlaza y carga módulos desde contenido en memoria (sin archivos).
        
        Args:
            contenidos: Diccionario {nombre_modulo: contenido_texto}
            direccion_base: Dirección base para cargar el código
            cargar_en_memoria: Si False, solo enlaza sin cargar a RAM
            
        Returns:
            True si todo fue exitoso
        """
        try:
            self.ultimo_error = None
            self.enlazador.limpiar()

            if self.verbose:
                print(f"[GESTOR] Procesando {len(contenidos)} módulo(s)...")

            # Procesa cada módulo
            for nombre, contenido in contenidos.items():
                try:
                    self.enlazador.agregar_archivo_modulo(contenido)
                    if self.verbose:
                        print(f"✓ Módulo cargado: {nombre}")
                except ErrorEnlazador as e:
                    self.ultimo_error = f"Error en {nombre}: {e}"
                    if self.verbose:
                        print(f"✗ {self.ultimo_error}")
                    return False

            # Enlaza
            try:
                if self.verbose:
                    print(f"[GESTOR] Enlazando módulos...")
                self.ultimo_binario = self.enlazador.enlazar(direccion_base)
                if self.verbose:
                    print(f"✓ Enlazado exitoso")
            except ErrorEnlazador as e:
                self.ultimo_error = f"Error en enlazador: {e}"
                if self.verbose:
                    print(f"✗ {self.ultimo_error}")
                return False

            # Carga en memoria
            if cargar_en_memoria:
                try:
                    if self.verbose:
                        print(f"[GESTOR] Cargando en memoria...")
                    exito = self.cargador.cargar(self.ultimo_binario, verbose=self.verbose)
                    if not exito:
                        self.ultimo_error = "Error al cargar en memoria"
                        return False
                    if self.verbose:
                        print(f"✓ Cargado en memoria exitosamente")
                except ErrorCargador as e:
                    self.ultimo_error = f"Error en cargador: {e}"
                    if self.verbose:
                        print(f"✗ {self.ultimo_error}")
                    return False

            return True

        except Exception as e:
            self.ultimo_error = f"Error inesperado: {e}"
            if self.verbose:
                print(f"✗ {self.ultimo_error}")
            return False

    def obtener_ultimo_error(self) -> Optional[str]:
        """Retorna el último error ocurrido"""
        return self.ultimo_error

    def obtener_ultimo_binario(self) -> Optional[BinarioEjectable]:
        """Retorna el último binario enlazado"""
        return self.ultimo_binario

    def obtener_tabla_simbolos(self) -> Dict:
        """Retorna la tabla de símbolos del último enlazado"""
        return self.enlazador.obtener_tabla_simbolos()


# Instancia global del gestor
gestor = GestorEnlazadorCargador(verbose=False)
