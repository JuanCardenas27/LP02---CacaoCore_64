import struct
from src.memoria.ram import ram, CODE_START, CODE_END, DATA_START, DATA_END, HEAP_START, STACK_END, WORD_SIZE
from .binario import BinarioEjectable, ErrorEnlazador


class ErrorCargador(ErrorEnlazador):
    pass


class ErrorValidacionMemoria(ErrorCargador):
    pass


class Cargador:
    def __init__(self, procesador=None):
        self.procesador = procesador
        self.interrupciones_activas = False
    
    def cargar(self, binario: BinarioEjectable) -> None:
        self._inicializacion()
        self._validar_encabezado(binario)
        self._copiar_codigo_y_datos(binario)
        self._inicializar_entorno(binario)
    
    def _inicializacion(self) -> None:
        self.interrupciones_activas = True
        if self.procesador:
            self._detener_uc_temporalmente()
        self._limpiar_registros_temporales()
        self._verificar_disponibilidad_ram()
    
    def _detener_uc_temporalmente(self) -> None:
        if hasattr(self.procesador, 'detenido'):
            self.procesador.detenido = True
    
    def _limpiar_registros_temporales(self) -> None:
        if self.procesador:
            if hasattr(self.procesador, '_mar'):
                self.procesador._mar[:] = bytes(4)
            if hasattr(self.procesador, '_mdr'):
                self.procesador._mdr[:] = bytes(6)
    
    def _verificar_disponibilidad_ram(self) -> None:
        if ram is None:
            raise ErrorValidacionMemoria("RAM no disponible")
    
    def _validar_encabezado(self, binario: BinarioEjectable) -> None:
        direccion_base = binario.direccion_base
        tam_codigo = len(binario.codigo)
        tam_datos = len(binario.datos)
        
        if direccion_base < CODE_START or direccion_base >= CODE_END:
            raise ErrorValidacionMemoria(
                f"Dirección base 0x{direccion_base:08X} fuera de rango de código "
                f"(0x{CODE_START:08X} – 0x{CODE_END-1:08X})"
            )
        
        if direccion_base + tam_codigo > CODE_END:
            raise ErrorValidacionMemoria(
                f"Código excede zona de código: "
                f"0x{direccion_base:08X} + {tam_codigo} bytes > 0x{CODE_END:08X}"
            )
        
        if DATA_START + tam_datos > DATA_END:
            raise ErrorValidacionMemoria(
                f"Datos exceden zona de datos estáticos: "
                f"0x{DATA_START:08X} + {tam_datos} bytes > 0x{DATA_END:08X}"
            )
        
        if direccion_base < 0x00001000:
            raise ErrorValidacionMemoria(
                f"Dirección base invade zona reservada de sistema"
            )
    
    def _copiar_codigo_y_datos(self, binario: BinarioEjectable) -> None:
        direccion_base = binario.direccion_base
        
        ram.unprotect_code()
        
        for offset, byte in enumerate(binario.codigo):
            direccion = direccion_base + offset
            ram._mem[direccion] = byte
        
        for offset, byte in enumerate(binario.datos):
            direccion = DATA_START + offset
            ram._mem[direccion] = byte
        
        ram.protect_code()
    
    def _inicializar_entorno(self, binario: BinarioEjectable) -> None:
        if self.procesador:
            direccion_base = binario.direccion_base
            
            pc = self.procesador._pc
            struct.pack_into("<Q", pc, 0, direccion_base)
            
            sp = self.procesador._registers[14] if len(self.procesador._registers) > 14 else None
            if sp:
                struct.pack_into("<Q", sp, 0, STACK_END - WORD_SIZE)
            
            acc = self.procesador._registers[15] if len(self.procesador._registers) > 15 else None
            if acc:
                acc[:] = bytes(8)
            
            fr = self.procesador._fr
            fr[:] = bytes(1)
            
            self.interrupciones_activas = False
            self._reanudar_uc()
    
    def _reanudar_uc(self) -> None:
        if self.procesador and hasattr(self.procesador, 'detenido'):
            self.procesador.detenido = False
