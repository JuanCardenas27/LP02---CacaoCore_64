import sys,traceback
sys.path.insert(0,'src')
from preprocesador import Preprocesador
from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import CODE_START
from cacao_core import CacaoCore64
from peripherals.io_controller import io_controller

if len(sys.argv) < 2:
    print('Usage: debug_established_example.py <path.choco>')
    sys.exit(2)

p = sys.argv[1]
print('Debug run:', p)
try:
    src = open(p, encoding='utf-8').read()
    pre = Preprocesador()
    res, imports = pre.preprocess(src, nombre_fuente=p)
    errs, asmc = compiler.compile_generator(res.text, imports.lista)
    print('Generator errors:', errs)
    open('resultado_debug.asm','w',encoding='utf-8').write('\n'.join(asmc))
    asm = Assembler()
    asm.process('\n'.join(asmc))
    reloc = asm.get_output()
    Linker().link_and_load(reloc, CODE_START, [])
    out = []
    io_controller.console = type('C',(object,),{'write_ok':lambda self,msg: out.append(msg)})()
    core = CacaoCore64()
    core.boot(CODE_START)
    core.run_full()
    print('OUT:', out[:10])
except Exception as e:
    print('Exception raised:')
    traceback.print_exc()
    print('\nException str:', str(e))
    sys.exit(1)
