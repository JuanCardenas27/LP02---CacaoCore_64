from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import ram, CODE_START
from cacao_core import CacaoCore64

with open('examples/high_level/semalyzer_tests/correct_example.choco','r',encoding='utf-8') as f:
    src = f.read()
errs, asmc = compiler.compile_generator(src, [])
reloc = '\n'.join(asmc)
asm = Assembler(); asm.process(reloc); reloc_out = asm.get_output()
linker = Linker(); out = linker.link_and_load(reloc_out, CODE_START, [])

core = CacaoCore64()
core.boot(CODE_START)
prev = core.processor._registers[2][:]
step = 0
try:
    while True:
        pc = int.from_bytes(core.processor._pc, byteorder='little', signed=False)
        core.run_step()
        step += 1
        curr = core.processor._registers[2][:]
        if curr != prev:
            print(f"Step {step} PC=0x{pc:04X} r2 changed: {prev.hex()} -> {curr.hex()}")
            # dump instruction at PC
            instr = ram.read(pc,8)
            print('instr@PC', instr.hex())
            prev = curr[:]
        if pc == 0x11E8:
            print('Reached target PC; r2=', curr.hex())
            break
except Exception as e:
    import traceback
    traceback.print_exc()
