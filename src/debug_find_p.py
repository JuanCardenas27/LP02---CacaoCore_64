from compiler.generador_codigo import GeneradorCodigo
p = GeneradorCodigo()
with open(r'c:\Users\secoe\Documents\Projects\CacaoCore\LP02---CacaoCore_64\src\examples\high_level\semalyzer_tests\correct_example.choco','r',encoding='utf-8') as f:
    src = f.read()
errors, asmc = p.parse(src, {})
for i,l in enumerate(asmc):
    if ' P' in l.upper() or '[P]' in l.upper() or 'P ' in l or '[p]' in l:
        print(f"{i+1:04}", l)
