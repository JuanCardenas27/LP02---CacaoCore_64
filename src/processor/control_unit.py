from memoria.ram import ram
from alu import ALU
from decoder import Decoder

class ControlUnit:

    _own_methods = {} # nombre (sin modo) : lambda x,y: self.name(x, [y])
    _mode_length = {
        "r": 4,
        "i": 16,
        "m": 32,
        "n": 4
    }

    def __init__(self):

        self._registers =[
            bytearray(8) for _ in range(0, 16)
        ]

        self._pc = bytearray(8)
        self._ir = bytearray(8)
        self._mar = bytearray(4)
        self._mdr = bytearray(6)
        self._fr = bytearray(1)
        self._dp = bytearray(1)

        self._alu = ALU(self._registers[15], self._fr)
        self._decoder = Decoder(self._dp)


    @staticmethod
    def _to_binary(number:bytearray, size, sign):
        number = int.from_bytes(number, byteorder='little', signed=sign)
        return f"{number:b}".zfill(size)

    def _fetch(self):
        self._mar[:] = self._pc[:]

        # TODO: Señal de READ en bus de control.

        # TODO: MDR <- Contenido bus de datos.

        self._ir[:] = self._mdr[:]

        acc = self._registers[15]
        self._alu.add(self._pc, (8).to_bytes(8, byteorder='little', signed=True))
        self._pc[:] = self._registers[15][:]
        self._registers[15][:] = acc[:]

        self._decode()
        
    def _decode(self):
        self._dp[:] = (0).to_bytes(1, byteorder='litle', signed=False)
        instruction, use_alu = self._decoder.decode(self._ir)
        name, modes = instruction.split('_')

        self._execute(name, modes, use_alu)

    def _execute(self, name, modes, use_alu):

        ops = [None for _ in range(2)]

        for i, mode in enumerate(modes):
            initial_pos = int.from_bytes(self._dp, byteorder='little', signed=False) * 4
            final_pos = initial_pos + self._mode_length[mode]
            cod_i = self._to_binary(self._ir, 64, False)[initial_pos: final_pos + 1]

            if mode == "r":
                ops[i] = self._registers[int(cod_i, 2)]

            elif mode == "i":
                ops[i] = bytearray(int(cod_i, 2).to_bytes(8, byteorder='little', signed=True))
            
            elif mode == "m":
                ops[i] = int(cod_i[::-1], 2)
            
            elif mode == "n":
                ops[i] = self._registers[int(cod_i[::-1], 2)]

        acc = self._registers[15]

        self._own_methods[name](ops[0], ops[1])

        # write-back

        self._registers[15][:] = acc[:]
        


    def _interruption_handler(self):
        pass


if __name__ == '__main__':
    proc = ControlUnit()
    print(proc._to_binary(bytearray([2,3]), 64))
