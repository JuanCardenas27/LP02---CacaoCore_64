from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import ram, CODE_START
from processor.control_unit import ControlUnit

# load and assemble
with open('examples/high_level/semalyzer_tests/correct_example.choco','r',encoding='utf-8') as f:
    src = f.read()
errs, asmc = compiler.compile_generator(src, [])
reloc = '\n'.join(asmc)
asm = Assembler(); asm.process(reloc); reloc_out = asm.get_output()
linker = Linker(); out = linker.link_and_load(reloc_out, CODE_START, [])
print('Linked.')
pc = 0x11E8
from memoria.ram import ram
wb = ram.read(pc,8)
print(f'RAM@0x{pc:04X} = {wb.hex()}')

# Show decode fields used by ControlUnit._execute
cu = ControlUnit()
cu._pc[:] = (pc).to_bytes(8,byteorder='little')
cu._mar[:] = cu._pc[:]
cu._read_from_ram()
instr = cu._mdr[:]
binstr = cu._to_binary(instr,64,False)
print('instr hex', instr.hex())
print('binstr', binstr)
print('first 32 bits:', binstr[:32])