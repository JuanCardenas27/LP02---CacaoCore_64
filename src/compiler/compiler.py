from .analizador_lexico import AnalizadorLexico
from .analizador_sintactico import AnalizadorSintactico


class Compiler:
    def __init__(self):
        self._lexer  = AnalizadorLexico()
        self._parser = AnalizadorSintactico()

    def compile(self, file_content: str):
        """
        Ejecuta el análisis léxico completo del código fuente.
        Retorna: (errores, tabla_de_simbolos, tokens)
        """
        errors, sym_table, tokens = self._lexer.analize(file_content)
        return errors, sym_table, tokens

    def parse(self, file_content: str):
        """
        Ejecuta el análisis léxico + sintáctico.
        Retorna: (errores, ast)
        """
        errors, ast = self._parser.parse(file_content)
        return errors, ast


# Instancia global
compiler = Compiler()