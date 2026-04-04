from .analizador_lexico import AnalizadorLexico

class Compiler:
    def __init__(self):
        self._lexer = AnalizadorLexico()
    
    def compile(self, file_content):
        # 1. Paso del analisis: Léxico
        tokens = self._lexer.analize(file_content)
        # TODO: los otros análisis
        print(tokens)
        return tokens


# Instancia global
compiler = Compiler()