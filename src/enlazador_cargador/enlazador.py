import struct
from .binario import Modulo, BinarioEjectable, SimboloNoDefinido, SimboloDuplicado, ErrorEnlazador


class Enlazador:
    def __init__(self):
        self.modulos = []
        self.tabla_simbolos_global = {}
        self.codigo_enlazado = bytearray()
        self.datos_enlazados = bytearray()
        self.mapeo_direcciones = {}
    
    def agregar_modulo(self, modulo: Modulo):
        if not isinstance(modulo, Modulo):
            raise ErrorEnlazador("Se esperaba un objeto Modulo")
        self.modulos.append(modulo)
    
    def enlazar(self, direccion_base: int = 0x00001000) -> BinarioEjectable:
        self._verificar_modulos()
        self._construir_tabla_simbolos_global()
        self._resolver_referencias()
        self._unificar_segmentos()
        
        binario = BinarioEjectable()
        binario.direccion_base = direccion_base
        binario.codigo = self.codigo_enlazado
        binario.datos = self.datos_enlazados
        
        return binario
    
    def _verificar_modulos(self):
        if not self.modulos:
            raise ErrorEnlazador("No hay módulos para enlazar")
    
    def _construir_tabla_simbolos_global(self):
        for modulo in self.modulos:
            for nombre, simbolo in modulo.simbolos_definidos.items():
                if nombre in self.tabla_simbolos_global:
                    raise SimboloDuplicado(f"Símbolo '{nombre}' definido múltiples veces")
                self.tabla_simbolos_global[nombre] = simbolo
    
    def _resolver_referencias(self):
        for modulo in self.modulos:
            for simbolo_externo, referencias in modulo.referencias_externas.items():
                if simbolo_externo not in self.tabla_simbolos_global:
                    raise SimboloNoDefinido(f"Símbolo '{simbolo_externo}' no definido")
                
                direccion_resuelta = self.tabla_simbolos_global[simbolo_externo].valor
                
                for posicion, tipo_operando in referencias:
                    if tipo_operando == "32bits":
                        struct.pack_into("<I", modulo.codigo, posicion, direccion_resuelta & 0xFFFFFFFF)
                    elif tipo_operando == "16bits":
                        struct.pack_into("<H", modulo.codigo, posicion, direccion_resuelta & 0xFFFF)
                    else:
                        raise ErrorEnlazador(f"Tipo de operando desconocido: {tipo_operando}")
    
    def _unificar_segmentos(self):
        self.codigo_enlazado = bytearray()
        self.datos_enlazados = bytearray()
        
        for modulo in self.modulos:
            self.codigo_enlazado.extend(modulo.codigo)
            self.datos_enlazados.extend(modulo.datos)
