from compiler import compiler
from assembler.assembler import Assembler

p = r'c:\Users\secoe\Documents\Projects\CacaoCore\LP02---CacaoCore_64\src\examples\high_level\Ejemplo_sustentacion.choco'
with open(p, encoding='utf-8') as f:
    s = f.read()

errs, asmc = compiler.compile_generator(s, [])
print('compile_ok', len(errs) == 0, 'errs', len(errs), 'asm_lines', len(asmc) if asmc else 0)
text = '\n'.join(asmc)
print('dict_literal_present', "{'kind':" in text)
print('has_k_decl', 'k : 0' in text)
print('has_i_decl', 'i : 0' in text)

asm = Assembler()
asm.process(text)
out = asm.get_output()
print('assemble_ok', True, 'out_lines', len(out.splitlines()))
