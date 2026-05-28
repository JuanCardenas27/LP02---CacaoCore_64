from compiler.generador_codigo import GeneradorCodigo
p = GeneradorCodigo()
with open(r'c:\Users\secoe\Documents\Projects\CacaoCore\LP02---CacaoCore_64\src\examples\high_level\semalyzer_tests\correct_example.choco','r',encoding='utf-8') as f:
    src = f.read()
errors, asmc = p.parse(src, {})
start=None
for i,l in enumerate(asmc):
    if l.strip().upper().startswith('ISADULT:'):
        start=i
        break
if start is None:
    print('ISADULT not found')
else:
    print('--- ISADULT ---')
    for j in range(start, start+80):
        if j < len(asmc):
            print(f"{j+1:04}", asmc[j])
