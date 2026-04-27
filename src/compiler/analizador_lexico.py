import ply.lex as lex

class AnalizadorLexico:
    tokens = (
        # Palabras clave
        'LET',        # let             - declarar variable (inmutable)
        'SET',        # set             - reasignar variable
        'FUNC',       # func            - definir función
        'IF',         # if              - condicional
        'OTHERWISE',  # otherwise       - else
        'ASLONGAS',   # asLongAs        - while
        'FOR',        # for             - for
        'IN',         # in              - for x in lista
        'DELIVER',    # deliver         - return
        'SHOW',       # show            - print
        'OOPS',       # oops            - throw / raise
    
        # Tipos de datos
        'INT_TYPE', # int               - tipo integer
        'FLOAT_TYPE', # float           - tipo flotante
        'TEXT_TYPE',  # text            - tipo string
        'BOOL_TYPE',  # bool            - tipo booleano
        'INT_LIT',    # 1               - valor entero
        'FLOAT_LIT',  # 1.0             - valor flotante
        'STRING',     # "hola mundo"
        'INDEED',     # indeed          - true booleano
        'NOPE',       # nope            - false booleano
        'NOTHING',    # nothing         - null/None
    
        # Identificadores
        'ID',         # nombres de variables y funciones
    
        # Operadores aritméticos
        'PLUS',       # +
        'MINUS',      # -
        'TIMES',      # *
        'DIVIDE',     # /
        'MOD',        # %
    
        # Operadores de comparación
        'EQ',         # ==
        'NEQ',        # !=
        'LT',         # <
        'GT',         # >
        'LEQ',        # <=
        'GEQ',        # >=

        # Operadores lógicos
        'OP_OR',      # or
        'OP_AND',     # and
        'OP_NOT',     # not
    
        # Asignación
        'ASSIGN',     # =
        'SWEET_PLUS',  # +=

    
        # Delimitadores
        'LPAREN',     # (
        'RPAREN',     # )
        'LBRACE',     # {
        'RBRACE',     # }
        'LBRACKET',   # [
        'RBRACKET',   # ]
        'COLON',      # :
        'COMMA',      # ,
        'DOT',        # .

        # Paradigma Orientado a Objetos
        'MOLD',       # class           - definición de TDA
        'OHMY',       # self            - referencia al objeto actual
        'SUMMON',     # new             - creación explícita

        # Referencias de Preprocesador
        'PREPRO_IMPORT',    # Referencia formateada de nombre de librería incluida que debe llegar al enlazador
        'PREPRO_EXTERN'     # Referencia formateada de nombre de símbolo incluido que debe llegar al enlazador
    )

    # Palabras reservadas para evitar que los ID las utlicen
    reserved = {
        'let':       'LET',
        'set':       'SET',
        'func':      'FUNC',
        'if':        'IF',
        'otherwise': 'OTHERWISE',
        'asLongAs':  'ASLONGAS',
        'for':       'FOR',
        'in':        'IN',
        'deliver':   'DELIVER',
        'show':      'SHOW',
        'oops':      'OOPS',
        'int':       'INT_TYPE',
        'float':     'FLOAT_TYPE',
        'text':      'TEXT_TYPE',
        'bool':      'BOOL_TYPE',
        'indeed':    'INDEED',
        'nope':      'NOPE',
        'or':        'OP_OR',
        'and':       'OP_AND',
        'not':       'OP_NOT',
        'nothing':   'NOTHING',
        'mold':      'MOLD',
        'ohmy':      'OHMY',
        'summon':    'SUMMON',
    }

    # Expresiones de preprocesador antes que DOT
    def t_PREPRO_IMPORT(self, t):
        r'\.import[^\n]*'
        return t

    def t_PREPRO_EXTERN(self, t):
        r'\.extern[^\n]*'
        return t

    t_EQ       = r'=='
    t_NEQ      = r'!='
    t_LEQ      = r'<='
    t_GEQ      = r'>='
    t_LT       = r'<'
    t_GT       = r'>'
    t_ASSIGN   = r'='
    t_SWEET_PLUS   = r'\+='
    t_PLUS     = r'\+'
    t_MINUS    = r'-'
    t_TIMES    = r'\*'
    t_DIVIDE   = r'/'
    t_MOD      = r'%'
    t_LPAREN   = r'\('
    t_RPAREN   = r'\)'
    t_LBRACE   = r'\{'
    t_RBRACE   = r'\}'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_COLON    = r':'
    t_COMMA    = r','
    t_DOT      = r'\.'
    t_ignore = ' \t'

    def __init__(self)      -> None:
        self.lexer = lex.lex(module=self)
        self.symbol_table = {}
        self.number_table = {}
        self.oops = []

    
    def t_FLOAT_LIT(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        self.number_table[t.value] = {
        'lexeme': t.value,        # "123", "3.14"
        'type': 'float',          # tipo del número
        'value': float(t.value),  # Valor ya convertido (float)
        'line' : [t.lineno],      # Dónde aparece
        }
        return t

    
    def t_INT_LIT(self, t):
        r'\d+'
        t.value = int(t.value)
        self.number_table[t.value] = {
        'lexeme': t.value,        # "123", "3.14"
        'type': 'int',            # tipo del número
        'value': int(t.value),    # Valor ya convertido (int)
        'line' : [t.lineno],      # Dónde aparece
        }
        return t
    
    @staticmethod
    def t_STRING(t):
        r'"[^"\n]*"'
        t.value = str(t.value)[1:-1]   # quitar comillas
        return t
    
    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = AnalizadorLexico.reserved.get(t.value, 'ID')

        if t.type == 'ID':
            if t.value not in self.symbol_table:
                self.symbol_table[t.value] = {
                    'lexeme': t.value,
                    'length': len(t.value),
                    'lines': [t.lineno],
                    'kind':  None, # Para el futuro, podría ser útil, indica su rol (si es variable, funcion, parametro, etc)
                    'type':  None, # Para el futuro, indica el tipo de dato (para variables unicamente) (int, float, str, bool)
                    'value': None, # Para el futuro, indica el valor inicial asignado (para variable unicamente)
                    'scope': None, # Para el futuro, indica el alcance de una definición (si es global o de una función)
                }
            else:
                self.symbol_table[t.value]['lines'].append(t.lineno)

        return t
    
    @staticmethod
    def t_COMMENT(t):
        r'//[^\n]*'
        pass

    @staticmethod
    def t_newline(t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        self.oops.append(f"Oops! Unknown character '{t.value[0]}' found at line {t.lexer.lineno}")
        t.lexer.skip(1)

    def analize(self, code):
        # Limpiar el lexer
        self.symbol_table = {}
        self.number_table = {}
        self.oops= []
        self.lexer.lineno = 1

        self.lexer.input(code)
        tokens = list(self.lexer)

        return self.oops, self.symbol_table, tokens


if __name__ == '__main__':

    lexer = AnalizadorLexico()
 
    sample_code = '''
// Programa de prueba
 
func greet(name: text) {
    show "Hello, " + name
    deliver nothing
}
 
let age: int = 25
let active: bool = indeed
 
if (age > 18) and (age < 65) {
    show "Welcome."
} otherwise {
    set active = nope
    show "Not today."
}
 
asLongAs age < 30 {
    set age = age + 1
}
 
show age

// Esto va a generar un error (que se llama formalmente un oops)
let precio: int = 10 @ 5
'''

    tokens = lexer.analize(sample_code)
    for tkn in tokens:
        print(tkn)
