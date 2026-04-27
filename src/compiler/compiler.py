from .analizador_lexico import AnalizadorLexico

class Compiler:
    def __init__(self):
        self._lexer = AnalizadorLexico()
    
    def compile(self, file_content:str):
        # 1. Paso del analisis: Léxico
        errors, sym_table, tokens, num_table = self._lexer.analize(file_content)
        # TODO: los otros análisis
        return errors, sym_table, tokens, num_table


# Instancia global
compiler = Compiler()