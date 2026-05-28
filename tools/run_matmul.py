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
# Post-process the generated asm to ensure any forward-declared data labels
# referenced via LEA exist in the .data section (best-effort). This helps
# avoid assembler KeyError when generator emits LEA to synthesized labels.
import re
asm_text = '\n'.join(asmc)
used_labels = set(re.findall(r'LEA\s+\w+,\s*\[(\w+)\]', asm_text))
lines = asm_text.splitlines()
if used_labels:
	# find .data section range
	try:
		data_idx = lines.index('.data')
	except ValueError:
		data_idx = -1
	if data_idx >= 0:
		existing = set()
		for ln in lines[data_idx+1:]:
			if ln.strip() == '.text':
				break
			m = re.match(r"(\w+)\s*:\s*", ln)
			if m:
				existing.add(m.group(1))
		inserts = []
		for lab in used_labels:
			if lab not in existing:
				inserts.append(f'{lab} : 0')
		if inserts:
			# insert after .data header
			lines = lines[:data_idx+1] + inserts + lines[data_idx+1:]
			asm_text = '\n'.join(lines)
			open('resultado_matmul.asm','w',encoding='utf-8').write(asm_text)
			# update asmc source for assembler input
			asmc = asm_text.splitlines()

asm.process('\n'.join(asmc))
reloc=asm.get_output()
Linker().link_and_load(reloc,CODE_START,[])
out=[]
io_controller.console=type('C',(object,),{'write_ok':lambda self,msg: out.append(msg)})()
core=CacaoCore64()
core.boot(CODE_START)
core.run_full()
print('outs', out)
