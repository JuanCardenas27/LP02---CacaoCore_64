from .analizador_lexico import AnalizadorLexico
from .analizador_sintactico import AnalizadorSintactico
from .analizador_semantico import AnalizadorSemantico
from .generador_codigo import GeneradorCodigo

class Compiler:
    def __init__(self):
        self._lexer = AnalizadorLexico()
        self._syntactic = AnalizadorSintactico()
        self._semantic = AnalizadorSemantico()
        self._generator = GeneradorCodigo()
    
    def compile_lexer(self, file_content:str):
        # 1. Paso del analisis: Léxico
        errors, sym_table, tokens, num_table = self._lexer.analize(file_content)
        return errors, sym_table, tokens, num_table
    
    def compile_syntactic(self, file_content:str):
        # 2. Paso del analisis: Sintáctico
        errors, ast = self._syntactic.parse(file_content)
        return errors, ast
    
    def compile_semantic(self, file_content:str, metadata:list):
        # 3. Paso del analisis: Semántico
        dict_s = self._semantic.parse(file_content, metadata)
        return dict_s['errors'], dict_s['ast'], dict_s['symbol_table']
    
    def compile_generator(self, file_content:str, metadata):
        # 4. Paso del analisis: Generación de código
        self._generator.funcs = []
        errors, asmc = self._generator.parse(file_content, metadata)
        return errors, asmc
    
    def compile_full(self, file_content:str, metadata):
        # 4. Paso del analisis: Generación de código
        errors, _, _, _ = self._lexer.analize(file_content)
        if errors:
            return errors
        errors, _ = self._syntactic.parse(file_content)
        if errors:
            return errors
        dict_s = self._semantic.parse(file_content, metadata)
        if dict_s['errors']:
            return errors
        errors, asmc = self._generator.parse(file_content, metadata)
        return errors, asmc


# Instancia global
compiler = Compiler()