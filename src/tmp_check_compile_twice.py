from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import ram, CODE_START

path = 'examples/high_level/semalyzer_tests/correct_example.choco'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

for run in (1, 2):
    errs, asmc = compiler.compile_generator(src, [])
    reloc = '\n'.join(asmc)
    asm = Assembler(); asm.process(reloc)
    reloc_out = asm.get_output()
    linker = Linker()
    linked = linker.link_and_load(reloc_out, CODE_START, [])
    first_word = ram.read(CODE_START, 8).hex()
    print(f'RUN {run}: errors={errs}')
    print(f'RUN {run}: first_word={first_word}')
    print(f'RUN {run}: first_linked_line={linked.splitlines()[-1] if linked.splitlines() else "<none>"}')
