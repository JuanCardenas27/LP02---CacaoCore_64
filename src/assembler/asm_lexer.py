import ply.lex as lex

# ASM's custom errors
class ASMLexicError(Exception):
    """Exception raised for lexic analysis."""
    pass

class AsmLexer:
    tokens = (
    'MNEMONIC', 'REGISTER', 'NUMBER', 'LABEL', 'COLON',
    'COMMA', 'LBRACKET', 'RBRACKET', 'NEWLINE', 'MEMORY',
    'SECTION', 'FLOAT', 'VAR', 'REFERENCE', 'QUOTE'
    )

    t_COLON    = r':'
    t_QUOTE    = r'\''
    t_COMMA    = r','
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_ignore   = ' \t'

    mnemonics = {
    'nop','hlt','ret','ei','di','iret','push','pop','intr',
    'movb','movh','movw','movd','swap',
    'loadb','loadh','loadw','loadd','lea',
    'storeb','storeh','storew','stored','sext',
    'add','sub','mul','div','inc','dec','neg',
    'and','or','xor','not','cmp','test',
    'shl','shr','rol','ror','cmpz',
    'jmp','jz','jnz','jc','jnc','js','jns','jo','jno',
    'jl','jg','jge','jle','call',
    'fpadd','fpsub','fpmul','fpdiv','fpneg','fpcmp',
    'fpsqrt','fptof','fptoi','ju','jnu'
    }
    def t_MEMORY(self, t):
        r'0x[0-9A-Fa-f]+'
        t.value = int(t.value, 16)
        return t
    
    def t_REFERENCE(self, t):
        r'"[^"]+"'
        return t
        
    def t_REGISTER(self, t):
        r'(R|r)(1[0-5]|[0-9])'
        t.value = int(t.value[1:])
        return t
    
    def t_SECTION(self, t):
        r'.DATA|.data|.TEXT|.text|.import|.IMPORT|.extern|.EXTERN'
        
        return t    
    
    def t_FLOAT(self, t):
        r'[+-]?(\d+\.\d+)'
        t.value = float(t.value)
        return t
    
    def t_NUMBER(self, t):
        r'[+-]?\d+'
        t.value = int(t.value)
        return t

    def t_NEWLINE(self, t):
        r'\n+'
        return t

    def t_VAR(self, t):
        r'[a-z_][a-z0-9_]*'
        
        value = t.value.lower()

        if value in self.mnemonics:
            t.type = 'MNEMONIC' 
            t.value = value
        else:
            t.type = 'VAR'

        return t    
    
    def t_LABEL(self, t):
        r'[A-Z_][A-Z0-9_]*'
        
        value = t.value.lower()

        if value in self.mnemonics:
            t.type = 'MNEMONIC' 
            t.value = value
        else:
            t.type = 'LABEL'

        return t    
    
    def t_COMMENT(self, t):
        r'(\#|\;)[^\n]*'
        pass
    
    def t_error(self, t):
        raise ASMLexicError(
        f"Token no identificado '{t.value[0]}' en línea {t.lineno}, posición {t.lexpos}"
        )

    def build(self):
        self.lexer = lex.lex(module=self)
        return self.lexer