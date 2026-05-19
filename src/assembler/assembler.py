from .asm_parser import AsmParser

class Assembler:

    def __init__(self):
        self.parser = AsmParser()
        self.output = None

    def process(self, lines):
        self.parser.parse(lines)

    def get_output(self):
        for elem in self.parser.pending:
            try:
                self.parser.program[elem[1]] = '{' + self.parser.symbol_table[elem[0]] + '}' + self.parser.program[elem[1]]
            except KeyError:
                self.parser.program[elem[1]] ='"@func ' + elem[0] + '"' + self.parser.program[elem[1]]
        print(self.parser.program)
        self.output = "\n".join(self.parser.program)
        return self.output

    def generate_file(self, file_name):
        with open(f"{file_name}", "w") as f:
            f.write("\n".join(self.parser.program))