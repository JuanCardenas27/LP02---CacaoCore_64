from .asm_parser import AsmParser

class Assembler:

    def __init__(self):
        self.parser = AsmParser()
        self.output = None

    def process(self, lines):
        # Instrument: log any asm lines containing '[nota]' so we can
        # correlate generator output to assembler processing when needed.
        try:
            text = lines if isinstance(lines, str) else "\n".join(lines)
            asm_lines = text.splitlines()
            for idx, l in enumerate(asm_lines):
                if '[nota]' in l:
                    try:
                        import json, traceback, time, os
                        entry = {
                            'time': time.time(),
                            'line_index': idx,
                            'line': l,
                            'stack': traceback.format_stack()[-8:]
                        }
                        with open(os.path.join(os.getcwd(), '.debug_asm_nota_lines.jsonl'), 'a', encoding='utf-8') as f:
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    except Exception:
                        pass
        except Exception:
            pass
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