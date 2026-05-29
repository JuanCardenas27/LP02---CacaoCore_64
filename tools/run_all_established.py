import sys, os, glob, json
sys.path.insert(0,'src')
from preprocesador import Preprocesador
from compiler import compiler
from assembler.assembler import Assembler
from enlazador_cargador.linker import Linker
from memoria.ram import CODE_START
from cacao_core import CacaoCore64
from peripherals.io_controller import io_controller

base = 'src/established_examples'
files = sorted(glob.glob(os.path.join(base,'*.choco')))
results = {}
for p in files:
    name = os.path.basename(p)
    print('---', name)
    try:
        src = open(p, encoding='utf-8').read()
        pre = Preprocesador()
        res, imports = pre.preprocess(src, nombre_fuente=p)
        errs, asmc = compiler.compile_generator(res.text, imports.lista)
        if errs:
            print('Generator errors:', errs)
            results[name] = {'status':'gen-error','errors':errs}
            continue
        asm = Assembler()
        try:
            asm.process('\n'.join(asmc))
        except Exception as e:
            print('Assembler exception:', e)
            results[name] = {'status':'asm-error','error':str(e)}
            continue
        reloc = asm.get_output()
        Linker().link_and_load(reloc, CODE_START, [])
        out = []
        io_controller.console = type('C',(object,),{'write_ok':lambda self,msg: out.append(msg)})()
        core = CacaoCore64()
        core.boot(CODE_START)
        core.run_full()
        print('OUT:', out[:10])
        results[name] = {'status':'ok','out':out}
    except Exception as e:
        print('Exception:', e)
        results[name] = {'status':'error','error':str(e)}

open('established_results.json','w',encoding='utf-8').write(json.dumps(results, indent=2))
print('\nSummary:')
for k,v in results.items():
    print(k, v['status'])
