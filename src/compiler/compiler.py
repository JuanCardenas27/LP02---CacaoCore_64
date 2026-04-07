from .analizador_lexico import AnalizadorLexico

class Compiler:
    def __init__(self):
        self._lexer = AnalizadorLexico()
    
    def compile(self, file_content:str):
        # 1. Paso del analisis: Léxico
        sym_table, tokens = self._lexer.analize(file_content)
        # TODO: los otros análisis
        return sym_table, tokens


# Instancia global
compiler = Compiler()