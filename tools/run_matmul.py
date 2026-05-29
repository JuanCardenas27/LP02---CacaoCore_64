import sys
sys.path.insert(0,'src')
from preprocesador import Preprocesador
from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import CODE_START
from cacao_core import CacaoCore64
from peripherals.io_controller import io_controller
p='src/examples/high_level/matmul.txt'
src=open(p,encoding='utf-8').read()
pre=Preprocesador()
res,imports=pre.preprocess(src, nombre_fuente=p)
errs,asmc=compiler.compile_generator(res.text, imports.lista)
print('errors', errs)
open('resultado_matmul.asm','w',encoding='utf-8').write('\n'.join(asmc))
asm=Assembler()
asm.process('\n'.join(asmc))
reloc=asm.get_output()
Linker().link_and_load(reloc,CODE_START,[])
out=[]
io_controller.console=type('C',(object,),{'write_ok':lambda self,msg: out.append(msg)})()
core=CacaoCore64()
core.boot(CODE_START)
core.run_full()
print('outs', out)
