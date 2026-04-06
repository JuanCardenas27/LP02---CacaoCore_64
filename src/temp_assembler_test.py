from assembler import ASM

with open("./examples/assembler/pre_asm.txt", "r") as f:
    contenido = f.read()
asm_mod = ASM()
asm_mod.process(contenido)
print(asm_mod.get_output())
asm_mod.generate_file('ex1.txt')
