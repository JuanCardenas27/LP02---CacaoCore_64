from isa.instructions import INSTRUCTION_SPECS

'''
r = 00
i = 01
m = 10
n = 11
'''

class Decoder:

    def __init__(self, dp):
        self._dp = dp
        self.bin2func = {}

    def _register(self):
        for instruction in INSTRUCTION_SPECS:
            node = self.bin2func

            hex_opcode = f"{instruction['opcode']:X}"  # sin 0x

            for char in hex_opcode:
                nibble = int(char, 16)
                node = node.setdefault(nibble, {})

            node["name"] = instruction["name"]
