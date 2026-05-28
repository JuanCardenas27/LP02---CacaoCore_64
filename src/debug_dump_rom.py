from cacao_core import CacaoCore64
from memoria.ram import SUBROUTINES, INTR_BUFFER, VECTOR_TABLE

cc = CacaoCore64()
cu = cc.processor

print('SUBROUTINES at', hex(SUBROUTINES))
# Dump first 32 instructions (words) at SUBROUTINES
addr = SUBROUTINES
for i in range(32):
    cu._mar[:] = addr.to_bytes(8, byteorder='little', signed=False)
    cu._read_from_ram()
    ir = cu._mdr[:]
    asm = cu._decoder.decode(ir)
    print(hex(addr), asm)
    addr += 8
