import os
import sys

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
)

from src.isa.microinstructions import MICROINSTRUCTION_SPECS

# from isa.instructions import INSTRUCTION_SPECS

class DecoderException(Exception):
    '''Error base para funcionalidades del decodificador.'''

class ISAOpcodesCollision(DecoderException):
    '''Colisión de los opcodes de la ISA con el método de decodificación actual.'''

class Decoder:

    def __init__(self, dp):
        self._dp = dp
        self.bin2func = {}
        self._register()

    def _register(self):
        for instruction in MICROINSTRUCTION_SPECS:
            node = self.bin2func

            hex_opcode = f"{instruction['opcode']:X}"  # sin 0x

            for char in hex_opcode:
                nibble = int(char, 16)
                node = node.setdefault(nibble, {})

            if "name" in node:
                raise ISAOpcodesCollision(
                    f'Instruction {instruction["name"]} has opcode {hex(instruction["opcode"])} '
                    f'already assigned to {node["name"]}, in current decoding method'
                )

            node["name"] = instruction["name"]

    def decode(self, opcode:bytearray):
        return (None,None)