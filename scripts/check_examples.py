import sys, os
sys.path.insert(0, 'src')
from preprocesador import Preprocesador
from compiler import compiler
from assembler.assembler import Assembler
from glob import glob
p = os.path.join('src','examples','high_level')
files = glob(os.path.join(p, '*.txt')) + glob(os.path.join(p, '*.choco'))
fails = []
for f in files:
    try:
        src = open(f, encoding='utf-8').read()
        pre = Preprocesador()
        res, imports = pre.preprocess(src, nombre_fuente=f)
        errs, asmc = compiler.compile_generator(res.text, imports.lista)
        if errs:
            fails.append((f, 'compile_errors', errs))
            continue
        asm = Assembler()
        asm.process('\n'.join(asmc))
    except Exception as e:
        fails.append((f, type(e).__name__, str(e)))

print('checked', len(files), 'files')
if fails:
    print('FAILS:')
    for it in fails:
        print(it[0], it[1])
        print(it[2][:400])
else:
    print('All good')
