from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import CODE_START

with open('examples/high_level/semalyzer_tests/correct_example.choco','r',encoding='utf-8') as f:
    src = f.read()
errs, asmc = compiler.compile_generator(src, [])
reloc = '\n'.join(asmc)
asm = Assembler(); asm.process(reloc); reloc_out = asm.get_output()
linker = Linker()
resolved_data, resolved_text = linker._resolve()
print('.text resolved:')
for i, w in enumerate(resolved_text):
    print(i, w.hex())
