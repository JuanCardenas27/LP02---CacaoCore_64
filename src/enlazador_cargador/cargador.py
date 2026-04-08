"""
Cargador Mejorado
=================
Carga binarios ejecutables en memoria del procesador.

Basado en cargador.py pero integrado con enlazador_mejorado.py
"""

import struct
from typing import Optional
from memoria.ram import ram, CODE_START, CODE_END, DATA_START, DATA_END, HEAP_START, STACK_END, WORD_SIZE
from .enlazador import BinarioEjectable, ErrorEnlazador


class ErrorCargador(ErrorEnlazador):
    """Excepción base para errores del cargador"""
    pass


class ErrorValidacionMemoria(ErrorCargador):
    """Error en validación de memoria o límites"""
    pass


class CargadorMejorado:
    """Cargador mejorado que integra validación con procesador"""

    def __init__(self, procesador=None):
        self.procesador = procesador
        self.interrupciones_activas = False
        self.ultima_direccion_cargada = 0

    def cargar(self, binario: BinarioEjectable, verbose: bool = False) -> bool:
        """
        Carga un binario ejecutable en memoria del procesador.
        
        Args:
            binario: BinarioEjectable resultado del enlazador
            verbose: Si True, imprime información de depuración
            
        Returns:
            True si la carga fue exitosa, False en caso contrario
            
        Raises:
            ErrorCargador: Si hay error en validación o carga
        """
        try:
            self._inicializacion()
            self._validar_encabezado(binario)
            self._copiar_codigo_y_datos(binario, verbose)
            self._inicializar_entorno(binario)

            self.ultima_direccion_cargada = binario.direccion_base + len(binario.codigo)
            return True

        except ErrorCargador as e:
            print(f"Error en cargador: {e}")
            return False
        finally:
            self._finalizacion()

    def _inicializacion(self) -> None:
        """Preparación inicial: detiene procesador, limpia registros"""
        self.interrupciones_activas = True

        if self.procesador:
            self._detener_uc_temporalmente()
            self._limpiar_registros_temporales()

        self._verificar_disponibilidad_ram()

    def _detener_uc_temporalmente(self) -> None:
        """Detiene el procesador (si existe) temporalmente"""
        if hasattr(self.procesador, 'detenido'):
            self.procesador.detenido = True

    def _limpiar_registros_temporales(self) -> None:
        """Limpia registros temporales del procesador"""
        if self.procesador:
            if hasattr(self.procesador, '_mar'):
                self.procesador._mar[:] = bytes(4)
            if hasattr(self.procesador, '_mdr'):
                self.procesador._mdr[:] = bytes(6)

    def _verificar_disponibilidad_ram(self) -> None:
        """Verifica que RAM esté disponible"""
        if ram is None:
            raise ErrorValidacionMemoria("RAM no disponible")

    def _validar_encabezado(self, binario: BinarioEjectable, verbose: bool = False) -> None:
        """
        Valida que el binario quepa en memoria disponible.
        
        Raises:
            ErrorValidacionMemoria: Si el binario no cabe o viola límites
        """
        direccion_base = binario.direccion_base
        tam_codigo = len(binario.codigo)
        tam_datos = len(binario.datos)

        # Validar rango de código
        if direccion_base < CODE_START or direccion_base >= CODE_END:
            raise ErrorValidacionMemoria(
                f"Dirección base 0x{direccion_base:08X} fuera de rango "
                f"(0x{CODE_START:08X} – 0x{CODE_END-1:08X})"
            )

        if direccion_base + tam_codigo > CODE_END:
            raise ErrorValidacionMemoria(
                f"Código excede zona de código: "
                f"0x{direccion_base:08X} + {tam_codigo} bytes > 0x{CODE_END:08X}"
            )

        # Validar rango de datos
        if DATA_START + tam_datos > DATA_END:
            raise ErrorValidacionMemoria(
                f"Datos exceden zona de datos: "
                f"0x{DATA_START:08X} + {tam_datos} bytes > 0x{DATA_END:08X}"
            )

        # Validar que no invada zona reservada
        if direccion_base < 0x00001000:
            raise ErrorValidacionMemoria(
                f"Dirección base invade zona reservada de sistema"
            )

        if verbose:
            print(f"✓ Validación exitosa: Código en 0x{direccion_base:08X} ({tam_codigo} bytes), "
                  f"Datos en 0x{DATA_START:08X} ({tam_datos} bytes)")

    def _copiar_codigo_y_datos(self, binario: BinarioEjectable, verbose: bool = False) -> None:
        """
        Copia código y datos a memoria RAM.
        """
        direccion_base = binario.direccion_base

        try:
            ram.unprotect_code()

            # Copiar código
            for offset, byte in enumerate(binario.codigo):
                direccion = direccion_base + offset
                ram._mem[direccion] = byte

            # Copiar datos
            for offset, byte in enumerate(binario.datos):
                direccion = DATA_START + offset
                ram._mem[direccion] = byte

            ram.protect_code()

            if verbose:
                print(f"✓ Código y datos copiados a RAM")

        except Exception as e:
            raise ErrorCargador(f"Error al copiar a RAM: {e}")

    def _inicializar_entorno(self, binario: BinarioEjectable) -> None:
        """
        Inicializa registros y estado del procesador.
        """
        if self.procesador:
            direccion_base = binario.direccion_base

            # Inicializar Program Counter
            if hasattr(self.procesador, '_pc'):
                pc = self.procesador._pc
                struct.pack_into("<Q", pc, 0, direccion_base)

            # Inicializar Stack Pointer
            if hasattr(self.procesador, '_registers') and len(self.procesador._registers) > 14:
                sp = self.procesador._registers[14]
                struct.pack_into("<Q", sp, 0, STACK_END - WORD_SIZE)

            # Limpiar Accumulator
            if hasattr(self.procesador, '_registers') and len(self.procesador._registers) > 15:
                acc = self.procesador._registers[15]
                acc[:] = bytes(8)

            # Limpiar Flags
            if hasattr(self.procesador, '_fr'):
                fr = self.procesador._fr
                fr[:] = bytes(1)

    def _finalizacion(self) -> None:
        """Limpieza final: reanuda procesador"""
        self.interrupciones_activas = False
        if self.procesador and hasattr(self.procesador, 'detenido'):
            self.procesador.detenido = False

    def obtener_ultima_direccion(self) -> int:
        """Retorna la última dirección donde se cargó código"""
        return self.ultima_direccion_cargada


# Instancia global del cargador
cargador = CargadorMejorado()
