import sys
sys.path.insert(0,'src')
from preprocesador import Preprocesador
from compiler import compiler
p='src/examples/high_level/matmul.txt'
src=open(p,encoding='utf-8').read()
pre=Preprocesador()
res,imports=pre.preprocess(src, nombre_fuente=p)
errs,ast,sym = compiler.compile_semantic(res.text, imports.lista)
print('rows_a:', sym.get('rows_a'))
print('cols_b:', sym.get('cols_b'))
print('c:', sym.get('c'))
