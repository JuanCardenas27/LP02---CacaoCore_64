import sys
sys.path.insert(0, 'src')

from preprocesador import Preprocesador
from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import CODE_START
from cacao_core import CacaoCore64
from peripherals.io_controller import io_controller

source = '''
func alfa() { deliver 1 }
func Alfa() { deliver 2 }
func ALFA() { deliver 3 }

show alfa()
show Alfa()
show ALFA()
'''

pre = Preprocesador()
res, imports = pre.preprocess(source, nombre_fuente='case_funcs')
errs, asmc = compiler.compile_generator(res.text, imports.lista)
print('errors', errs)
open('resultado_case_funcs.asm', 'w', encoding='utf-8').write('\n'.join(asmc))

asm = Assembler()
asm.process('\n'.join(asmc))
reloc = asm.get_output()
Linker().link_and_load(reloc, CODE_START, [])

out = []
io_controller.console = type('C', (object,), {'write_ok': lambda self, msg: out.append(msg)})()
core = CacaoCore64()
core.boot(CODE_START)
core.run_full()
print('outs', out)
