import sys
import builtins
sys.path.insert(0, 'src')
from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import CODE_START
from cacao_core import CacaoCore64
from peripherals.io_controller import io_controller

src = """let a: int[2][2] = 1,2,3,4
set a[0][0] += 5
show a[0][0]
"""
errs, asmc = compiler.compile_generator(src, [])
print('errors', errs)
for idx, line in enumerate(asmc):
    if 'ADD' in line or 'MOVD' in line or 'MUL' in line or 'INTR 0' in line:
        print(idx, line)
asm = Assembler()
asm.process('\n'.join(asmc))
reloc = asm.get_output()
Linker().link_and_load(reloc, CODE_START, [])
out = []
io_controller.console = type('C', (object,), {'write_ok': lambda self, msg: out.append(msg)})()
core = CacaoCore64()
core.boot(CODE_START)
op = builtins.print
builtins.print = lambda *a, **k: None
core.run_full()
builtins.print = op
print('outs', out)
