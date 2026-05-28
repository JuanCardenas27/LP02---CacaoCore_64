import sys, traceback
# Ensure src is in path
sys.path.insert(0, '')
from compiler import compiler
from enlazador_cargador.linker import Linker
from assembler.assembler import Assembler
from memoria.ram import CODE_START
from cacao_core import CacaoCore64

# Read source
with open('examples/high_level/semalyzer_tests/correct_example.choco', 'r', encoding='utf-8') as f:
    src = f.read()

# Compile to reloc
errs, asmc = compiler.compile_generator(src, [])
print('Compile errors:', errs)

reloc = '\n'.join(asmc)

# Run assembler to convert .data declarations into hex words
asm_mod = Assembler()
asm_mod.process(reloc)
reloc = asm_mod.get_output()
with open('tmp_reloc_assembled.txt','w',encoding='utf-8') as f:
    f.write(reloc)

# Optional: write reloc to tmp file for inspection
with open('tmp_reloc_output.txt', 'w', encoding='utf-8') as f:
    f.write(reloc)

# Link and load
linker = Linker()
try:
    out = linker.link_and_load(reloc, CODE_START, [])
    print('Link output:\n', out)
except Exception:
    print('Exception during linking:')
    traceback.print_exc()

# Boot and run
compu = CacaoCore64()
compu.boot(CODE_START)
try:
    compu.run_full()
except Exception:
    print('Exception during execution:')
    traceback.print_exc()
