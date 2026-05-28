from compiler import compiler

p = r'c:\Users\secoe\Documents\Projects\CacaoCore\LP02---CacaoCore_64\src\examples\high_level\Ejemplo_sustentacion.choco'
with open(p, encoding='utf-8') as f:
    s = f.read()

errs, asmc = compiler.compile_generator(s, [])
text = '\n'.join(asmc)
print('ok', len(errs) == 0, 'errs', len(errs), 'asm_lines', len(asmc) if asmc else 0)
print('dict_literal_present', "{'kind':" in text)
for line in asmc:
    if line.startswith('MOVD [k],') or line.startswith('MOVD [i],'):
        print(line)
