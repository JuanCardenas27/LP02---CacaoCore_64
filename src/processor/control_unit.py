from alu import ALU
from decoder import Decoder

class ControlUnit:
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
    def _to_binary(number, size):
        return f"{number:{size}b}"
    
    def _get_register(self, bin):
        '''
        This method returns the value stored inside an specified register

        '''
        return self._registers[bin]




if __name__ == '__main__':
    proc = ControlUnit()
    print(proc._get_register(proc._to_binary(2)))
