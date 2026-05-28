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
pc_target = 0x11E8
step = 0
try:
    while True:
        pc = int.from_bytes(core.processor._pc, byteorder='little', signed=False)
        if pc == pc_target:
            print('Reached PC target at step', step)
            # dump registers
            for i, reg in enumerate(core.processor._registers):
                print(f'r{i}: {reg.hex()}')
            print('SP:', core.processor._registers[13].hex())
            print('PC:', core.processor._pc.hex())
            # dump memory around SP
            sp = int.from_bytes(core.processor._registers[13], byteorder='little', signed=False)
            print('RAM @ SP:', ram.dump(sp, 64))
            break
        core.run_step()
        step += 1
except Exception as e:
    import traceback
    traceback.print_exc()
