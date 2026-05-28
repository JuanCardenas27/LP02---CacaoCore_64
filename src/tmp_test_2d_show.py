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
show a[0][0]
show a[0][1]
show a[1][0]
show a[1][1]
"""
errs, asmc = compiler.compile_generator(src, [])
print('errors', errs)
print('show-lines', [line for line in asmc if 'INTR 0' in line or 'MOVD R10' in line or 'MOVD R11' in line or 'MOVD R12' in line])
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
