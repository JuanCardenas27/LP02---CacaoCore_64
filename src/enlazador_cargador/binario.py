import struct


class ErrorEnlazador(Exception):
    pass


class SimboloNoDefinido(ErrorEnlazador):
    pass


class SimboloDuplicado(ErrorEnlazador):
    pass


class ErrorValidacionBinario(ErrorEnlazador):
    pass


class BinarioEjectable:
    def __init__(self):
        self.direccion_base = 0
        self.codigo = bytearray()
        self.datos = bytearray()
    
    def serializar(self) -> bytes:
        resultado = bytearray()
        resultado.extend(struct.pack("<Q", self.direccion_base))
        resultado.extend(struct.pack("<Q", len(self.codigo)))
        resultado.extend(self.codigo)
        resultado.extend(struct.pack("<Q", len(self.datos)))
        resultado.extend(self.datos)
        return bytes(resultado)
    
    @staticmethod
    def deserializar(datos: bytes) -> 'BinarioEjectable':
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


class Simbolo:
    def __init__(self, nombre: str, tipo: str, valor: int):
        self.nombre = nombre
        self.tipo = tipo
        self.valor = valor


class Modulo:
    def __init__(self):
        self.codigo = bytearray()
        self.datos = bytearray()
        self.simbolos_definidos = {}
        self.referencias_externas = {}
    
    def agregar_simbolo(self, nombre: str, tipo: str, valor: int):
        if nombre in self.simbolos_definidos:
            raise SimboloDuplicado(f"Símbolo '{nombre}' ya definido en este módulo")
        self.simbolos_definidos[nombre] = Simbolo(nombre, tipo, valor)
    
    def agregar_referencia_externa(self, nombre: str, posicion: int, tipo_operando: str):
        if nombre not in self.referencias_externas:
            self.referencias_externas[nombre] = []
        self.referencias_externas[nombre].append((posicion, tipo_operando))
