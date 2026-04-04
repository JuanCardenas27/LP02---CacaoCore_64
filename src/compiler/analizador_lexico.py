import ply.lex as lex

class AnalizadorLexico:
    tokens = (
        # Palabras clave
        'LET',        # let       - declarar variable (inmutable)
        'SET',        # set       - reasignar variable
        'FUNC',       # func      - definir función
        'IF',         # if        - condicional
        'OTHERWISE',  # otherwise - else
        'ASLONGAS',   # asLongAs  - while
        'FOR',        # for       - for
        'IN',         # in        - for x in lista
        'DELIVER',    # deliver   - return
        'SHOW',       # show      - print
        'OOPS',       # oops      - throw / raise
    
        # Tipos de datos
        'INT_TYPE', # int            - tipo integer
        'FLOAT_TYPE', # float        - tipo flotante
        'TEXT_TYPE',  # text    - tipo string
        'BOOL_TYPE',  # bool    - tipo booleano
        'STRING',     # "hola mundo"
        'INDEED',     # indeed    - true booleano
        'NOPE',       # nope      - false booleano
        'NOTHING',    # nothing   - null/None
    
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
    
        # Asignación
        'ASSIGN',     # =
    
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
        'announce':  'ANNOUNCE',
        'oops':      'OOPS',
        'int':       'INT_TYPE',
        'float':     'FLOAT_TYPE',
        'text':      'TEXT_TYPE',
        'bool':      'BOOL_TYPE',
        'indeed':    'INDEED',
        'nope':      'NOPE',
        'nothing':   'NOTHING',
    }

    t_EQ       = r'=='
    t_NEQ      = r'!='
    t_LEQ      = r'<='
    t_GEQ      = r'>='
    t_LT       = r'<'
    t_GT       = r'>'
    t_ASSIGN   = r'='
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

    @staticmethod
    def t_FLOAT_TYPE(t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    @staticmethod
    def t_INT_TYPE(t):
        r'\d+'
        t.value = int(t.value)
        return t
    
    @staticmethod
    def t_STRING(t):
        r'"[^"\n]*"'
        t.value = str(t.value)[1:-1]   # quitar comillas
        return t
    
    @staticmethod
    def t_ID(t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = AnalizadorLexico.reserved.get(t.value, 'ID')
        return t
    
    @staticmethod
    def t_COMMENT(t):
        r'//[^\n]*'
        pass

    @staticmethod
    def t_newline(t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    @staticmethod
    def t_error(t):
        print(f"oops! Unknown character '{t.value[0]}' found at line {t.lexer.lineno}")
        t.lexer.skip(1)

    def analize(self, code):
        self.lexer.input(code)
        return list(self.lexer)

    def __init__(self) -> None:
        self.lexer = lex.lex(module=self)

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
 
if age > 18 {
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
