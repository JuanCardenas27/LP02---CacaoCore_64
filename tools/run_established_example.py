import sys
sys.path.insert(0,'src')
from preprocesador import Preprocesador
from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import CODE_START
from cacao_core import CacaoCore64
from peripherals.io_controller import io_controller

if len(sys.argv) < 2:
    print('Usage: run_established_example.py <path.choco>')
    sys.exit(2)

p = sys.argv[1]
print('Running example:', p)
src = open(p, encoding='utf-8').read()
pre = Preprocesador()
res, imports = pre.preprocess(src, nombre_fuente=p)
errs, asmc = compiler.compile_generator(res.text, imports.lista)
print('Generator errors:', errs)
open('resultado_example.asm','w',encoding='utf-8').write('\n'.join(asmc))
asm = Assembler()
try:
    asm.process('\n'.join(asmc))
except Exception as e:
    print('Assembler error:', e)
    raise
reloc = asm.get_output()
Linker().link_and_load(reloc, CODE_START, [])
out = []
io_controller.console = type('C',(object,),{'write_ok':lambda self,msg: out.append(msg)})()
core = CacaoCore64()
core.boot(CODE_START)
core.run_full()
print('outs', out)
