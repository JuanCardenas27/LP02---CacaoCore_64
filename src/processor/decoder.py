"""
decoder.py — Decodificador de Instrucciones ISA
=================================================
Realiza la decodificacion de instrucciones de maquina segun la ISA registrada.

Mecanismo de decodificacion
---------------------------
Construye un arbol binario (nibble-based) que representa la estructura jerarquica
de los opcodes definidos en MICROINSTRUCTION_SPECS. Cada nivel del arbol representa
un nibble (4 bits) del opcode.

Detecta automaticamente colisiones de opcode y prefijos conflictivos durante la
registracion.

Uso tipico
----------
    decoder = Decoder(dp)              # dp es un bytearray de 1 byte (DP register)
    instr_name = decoder.decode(instruction_bytes)
    print(instr_name)                  # ej: "add_rr", "movb_nr", etc.
"""

from isa.microinstructions import MICROINSTRUCTION_SPECS

class DecoderException(Exception):
    """Error base para funcionalidades del decodificador."""

class ISAOpcodesCollision(DecoderException):
    """
    Colision de opcodes en la ISA.
    
    Se lanza cuando hay conflictos entre definiciones de opcode, como:
    - Un opcode extiende una instruccion ya registrada
    - Dos instrucciones comparten el mismo opcode
    - Un opcode es prefijo de otro
    """

class InvalidOpcode(DecoderException):
    """
    Opcode invalido o inexistente.
    
    Se lanza cuando:
    - Un nibble de la secuencia de opcode no coincide con ningun opcode registrado
    - La secuencia de opcode es incompleta despues de procesar 64 bits
    """

class Decoder:
    """
    Decodificador de instrucciones segun la ISA definida.
    
    Construye un arbol de decodificacion nibble-based a partir de MICROINSTRUCTION_SPECS
    y utiliza este arbol para traducir secuencias de bytes en nombres de instrucciones.
    
    Atributos
    ---------
    _dp : bytearray
        Referencia al registro DP (Decode Pointer) de 1 byte que se incrementa
        durante la decodificacion.
    _bin2func_tree : dict
        Arbol jerarquico de decodificacion donde cada nivel representa un nibble
        del opcode. Las hojas contienen el nombre de la instruccion.
    
    Uso tipico
    ----------
        decoder = Decoder(bytearray([0]))  # DP inicial en 0
        try:
            name = decoder.decode(instruction_bytes)
            print(f"Instruccion: {name}")
        except InvalidOpcode as e:
            print(f"Error: {e}")
    """

    def __init__(self, dp):
        """
        Inicializa el decodificador con el registro DP.
        
        Construye el árbol de decodificación a partir de MICROINSTRUCTION_SPECS
        de forma automática. Detecta colisiones de opcodes y fallará si existen
        opcodes conflictivos.
        
        Parámetros
        ----------
        dp : bytearray
            Referencia al registro DP (Decode Pointer) de 1 byte que será
            incrementado durante la decodificación.
        
        Lanza
        -----
        ISAOpcodesCollision
            Si hay conflictos entre opcodes (prefijos superpuestos, duplicados).
        """
        self._dp = dp
        self._bin2func_tree = {}
        self._register()

    def _register(self):
        """
        Construye el arbol de decodificacion a partir de MICROINSTRUCTION_SPECS.
        
        Itera sobre cada instruccion, convierte su opcode a hexadecimal y construye
        un arbol jerarquico donde cada nivel representa un nibble (4 bits) del opcode.
        
        Valida automaticamente que no haya colisiones de opcodes durante el registro.
        
        Lanza
        -----
        ISAOpcodesCollision
            Si detecta opcodes conflictivos, prefijos superpuestos, o instrucciones
            duplicadas.
        """
        for instruction in MICROINSTRUCTION_SPECS:
            node = self._bin2func_tree

            hex_opcode = f"{instruction['opcode']:X}"  # sin 0x

            for char in hex_opcode:
                nibble = int(char, 16)

                if "name" in node:
                    raise ISAOpcodesCollision(
                        f'El opcode {hex(instruction["opcode"])} '
                        f'extiende una instrucción ya registrada {node["name"]}'
                    )

                node = node.setdefault(nibble, {})

            if "name" in node:
                raise ISAOpcodesCollision(
                    f'La instrucción {instruction["name"]} tiene opcode {hex(instruction["opcode"])} '
                    f'ya asignado a {node["name"]}, en el método de decodificación actual'
                )
            
            if node:
                raise ISAOpcodesCollision(
                    f'El opcode {hex(instruction["opcode"])} '
                    f'es prefijo de otra instrucción'
                )

            node["name"] = instruction["name"]

    def decode(self, instruction: bytearray) -> str:
        """
        Decodifica una instruccion de maquina a su nombre simbolico.
        
        Procesa la instruccion byte a byte, extrayendo nibbles y navegando por el
        arbol de decodificacion. Incrementa DP en cada nibble procesado.
        Nota: La instruccion se procesa en big-endian (se invierte antes de decodificar).
        
        Parametros
        ----------
        instruction : bytearray
            Bytes de la instruccion a decodificar (maximo 8 bytes = 64 bits).
        
        Retorna
        -------
        str
            Nombre de la instruccion decodificada.
        
        Lanza
        -----
        InvalidOpcode
            Si un nibble de la secuencia no coincide con ningun opcode registrado,
            o si la secuencia es incompleta tras procesar los 64 bits.
        """
        instruction = instruction[::-1] # El formato de instruccion se decodifica en big endian
        node = self._bin2func_tree

        for byte in instruction:
            for nibble in (byte >> 4, byte & 0x0F):

                if nibble not in node:
                    raise InvalidOpcode(
                        f'El nibble {hex(nibble)} de la secuencia de opcode en '
                        f'{instruction} no coincide con ningún opcode existente'
                    )

                node = node[nibble]
                new_dp_value = int.from_bytes(self._dp, byteorder='little', signed=False) + 1
                self._dp[:] = new_dp_value.to_bytes(1, byteorder='little', signed=False)

                if "name" in node:
                    return node["name"]

        raise InvalidOpcode(
            f'La secuencia de opcode en {instruction} fue leída '
            f'como un opcode de longitud completa (64 bits) que permanece incompleto'
        )
