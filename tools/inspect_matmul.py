import sys
sys.path.insert(0,'src')
from preprocesador import Preprocesador
from compiler import compiler
p='src/examples/high_level/matmul.txt'
src=open(p,encoding='utf-8').read()
pre=Preprocesador()
res,imports=pre.preprocess(src, nombre_fuente=p)
errs,asmc=compiler.compile_generator(res.text, imports.lista)
print('errors', errs)
for i,line in enumerate(asmc):
    if any(x in line for x in ('ADD','MOVD','MUL','FPADD','FPMUL','FP')):
        print(f'{i:04d}: {line}')
    # Also print surrounding context for first few hits
# print selected region for focused inspection
print('\n--- region 0080..0115 ---')
for i in range(80,116):
    print(f'{i:04d}: {asmc[i]}')
# print full for manual inspection if needed
#print('\n'.join(f"{i:04d}: {l}" for i,l in enumerate(asmc)))
