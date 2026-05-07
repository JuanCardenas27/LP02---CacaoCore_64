"""
analizador_sintactico.py
========================
Analizador Sintáctico (Parser) LALR(1) para CacaoScript — CACAO_Core-64.
Construido con PLY (Python Lex-Yacc).

Gramática en E-BNF:
──────────────────────────────────────────────────────────────────
program         ::= { statement }

statement       ::= let_stmt
                  | set_stmt
                  | func_def
                  | mold_def
                  | if_stmt
                  | while_stmt
                  | for_stmt
                  | deliver_stmt
                  | show_stmt
                  | oops_stmt
                  | expr_stmt

let_stmt        ::= 'let' ID ':' type_annot [ dims ] [ '=' initializer ]
dims            ::= '[' expr ']' [ '[' expr ']' ]
initializer     ::= expr | value_list
value_list      ::= expr { ',' expr }          (* ≥ 2 elementos *)

set_stmt        ::= 'set' lvalue ( '=' | '+=' ) expr

lvalue          ::= ID { '[' expr ']' } { '.' ID }

type_annot      ::= 'int' | 'float' | 'text' | 'bool' | ID

func_def        ::= 'func' ID '(' [ param_list ] ')' block
param_list      ::= param { ',' param }
param           ::= ID ':' type_annot

mold_def        ::= 'mold' ID '{' { mold_member } '}'
mold_member     ::= let_stmt | func_def

if_stmt         ::= 'if' expr block [ 'otherwise' block ]
while_stmt      ::= 'asLongAs' expr block
for_stmt        ::= 'for' '(' for_init ',' expr ',' for_update ')' block
for_init        ::= let_stmt_simple
for_update      ::= set_stmt_simple | expr

deliver_stmt    ::= 'deliver' [ expr ]
show_stmt       ::= 'show' expr
oops_stmt       ::= 'oops' expr
expr_stmt       ::= expr

block           ::= '{' { statement } '}'

expr            ::= expr ( '+' | '-' | '*' | '/' | '%' ) expr
                  | expr ( '==' | '!=' | '<' | '>' | '<=' | '>=' ) expr
                  | expr ( 'and' | 'or' | 'xor' ) expr
                  | 'not' expr
                  | '-' expr
                  | expr '[' expr ']'
                  | expr '.' ID '(' [ arg_list ] ')'
                  | expr '.' ID
                  | ID '(' [ arg_list ] ')'
                  | 'summon' ID '(' [ arg_list ] ')'
                  | 'ohmy' [ '.' ID ]
                  | '(' expr ')'
                  | ID | INT_LIT | FLOAT_LIT | STRING
                  | 'indeed' | 'nope' | 'nothing'

arg_list        ::= expr { ',' expr }
──────────────────────────────────────────────────────────────────
"""

import ply.yacc as yacc
from .analizador_lexico import AnalizadorLexico
from .ast_nodos import (
    NodoPrograma, NodoDeclaracion, NodoReasignacion, NodoFuncion, NodoMold,
    NodoSi, NodoMientras, NodoPara, NodoEntregar, NodoMostrar, NodoOops,
    NodoPreprocesador, NodoBloque, NodoBinario, NodoUnario, NodoLlamada,
    NodoAccesoMiembro, NodoAccesoArreglo, NodoSummon, NodoListaValores,
    NodoID, NodoEntero, NodoFlotante, NodoCadena, NodoBooleano, NodoNada,
    NodoOhmy,
)


class AnalizadorSintactico:
    """
    Parser LALR(1) para CacaoScript.

    Uso:
        parser = AnalizadorSintactico()
        errores, ast = parser.parse(codigo_fuente)
    """

    # ── Tokens (lista completa del lenguaje) ───────────────────────────────
    tokens = AnalizadorLexico.tokens

    # ── Precedencia (de menor a mayor) ────────────────────────────────────
    precedence = (
        ('left',  'OR'),
        ('left',  'AND'),
        ('right', 'NOT'),
        ('left',  'EQ', 'NEQ'),
        ('left',  'LT', 'GT', 'LEQ', 'GEQ'),
        ('left',  'PLUS', 'MINUS'),
        ('left',  'TIMES', 'DIVIDE', 'MOD'),
        ('right', 'UMINUS'),
        ('left',  'LBRACKET'),
        ('left',  'DOT'),
    )

    # ══════════════════════════════════════════════════════════════════════
    # PROGRAMA
    # ══════════════════════════════════════════════════════════════════════

    def p_program(self, p):
        """program : stmt_list"""
        p[0] = NodoPrograma(p[1])

    def p_stmt_list_multi(self, p):
        """stmt_list : stmt_list statement"""
        p[0] = p[1] + [p[2]]

    def p_stmt_list_empty(self, p):
        """stmt_list : empty"""
        p[0] = []

    # ══════════════════════════════════════════════════════════════════════
    # SENTENCIAS
    # ══════════════════════════════════════════════════════════════════════

    def p_statement(self, p):
        """statement : let_stmt
                     | set_stmt
                     | func_def
                     | mold_def
                     | if_stmt
                     | while_stmt
                     | for_stmt
                     | deliver_stmt
                     | show_stmt
                     | oops_stmt
                     | expr_stmt"""
        p[0] = p[1]

    # ── Declaración let ───────────────────────────────────────────────────

    def p_let_simple(self, p):
        """let_stmt : LET ID COLON type_annot"""
        p[0] = NodoDeclaracion(p[2], p[4], linea=p.lineno(1))

    def p_let_with_val(self, p):
        """let_stmt : LET ID COLON type_annot ASSIGN initializer"""
        p[0] = NodoDeclaracion(p[2], p[4], valor=p[6], linea=p.lineno(1))

    def p_let_array_1d(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET"""
        p[0] = NodoDeclaracion(p[2], p[4], dim1=p[6], linea=p.lineno(1))

    def p_let_array_1d_val(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET ASSIGN initializer"""
        p[0] = NodoDeclaracion(p[2], p[4], dim1=p[6], valor=p[9], linea=p.lineno(1))

    def p_let_array_2d(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET LBRACKET expr RBRACKET"""
        p[0] = NodoDeclaracion(p[2], p[4], dim1=p[6], dim2=p[9], linea=p.lineno(1))

    def p_let_array_2d_val(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET LBRACKET expr RBRACKET ASSIGN initializer"""
        p[0] = NodoDeclaracion(p[2], p[4], dim1=p[6], dim2=p[9], valor=p[12], linea=p.lineno(1))

    # Inicializador: expresión simple o lista de valores separada por comas

    def p_initializer_expr(self, p):
        """initializer : expr"""
        p[0] = p[1]

    def p_initializer_list(self, p):
        """initializer : value_list"""
        p[0] = p[1]

    def p_value_list_start(self, p):
        """value_list : expr COMMA expr"""
        p[0] = NodoListaValores([p[1], p[3]], linea=p.lineno(2))

    def p_value_list_grow(self, p):
        """value_list : value_list COMMA expr"""
        p[1].valores.append(p[3])
        p[0] = p[1]

    # ── Tipo anotación ────────────────────────────────────────────────────

    def p_type_int(self, p):
        """type_annot : INT_TYPE"""
        p[0] = 'int'

    def p_type_float(self, p):
        """type_annot : FLOAT_TYPE"""
        p[0] = 'float'

    def p_type_text(self, p):
        """type_annot : TEXT_TYPE"""
        p[0] = 'text'

    def p_type_bool(self, p):
        """type_annot : BOOL_TYPE"""
        p[0] = 'bool'

    def p_type_id(self, p):
        """type_annot : ID"""
        p[0] = p[1]

    # ── Reasignación set ──────────────────────────────────────────────────

    def p_set_assign(self, p):
        """set_stmt : SET lvalue ASSIGN expr"""
        p[0] = NodoReasignacion(p[2], '=', p[4], linea=p.lineno(1))

    def p_set_pluseq(self, p):
        """set_stmt : SET lvalue SWEET_PLUS expr"""
        p[0] = NodoReasignacion(p[2], '+=', p[4], linea=p.lineno(1))

    # ── Lvalue ────────────────────────────────────────────────────────────

    def p_lvalue_id(self, p):
        """lvalue : ID"""
        p[0] = NodoID(p[1], linea=p.lineno(1))

    def p_lvalue_ohmy(self, p):
        """lvalue : OHMY"""
        p[0] = NodoOhmy(linea=p.lineno(1))

    def p_lvalue_array_1d(self, p):
        """lvalue : lvalue LBRACKET expr RBRACKET"""
        if isinstance(p[1], NodoAccesoArreglo):
            p[1].indices.append(p[3])
            p[0] = p[1]
        else:
            p[0] = NodoAccesoArreglo(p[1], [p[3]], linea=p.lineno(2))

    def p_lvalue_member(self, p):
        """lvalue : lvalue DOT ID"""
        p[0] = NodoAccesoMiembro(p[1], p[3], linea=p.lineno(2))

    # ── Función ───────────────────────────────────────────────────────────

    def p_func_def(self, p):
        """func_def : FUNC ID LPAREN param_list RPAREN block"""
        p[0] = NodoFuncion(p[2], p[4], p[6], linea=p.lineno(1))

    def p_func_def_no_params(self, p):
        """func_def : FUNC ID LPAREN RPAREN block"""
        p[0] = NodoFuncion(p[2], [], p[5], linea=p.lineno(1))

    def p_param_list_one(self, p):
        """param_list : param"""
        p[0] = [p[1]]

    def p_param_list_many(self, p):
        """param_list : param_list COMMA param"""
        p[0] = p[1] + [p[3]]

    def p_param(self, p):
        """param : ID COLON type_annot"""
        p[0] = (p[1], p[3])

    # ── Mold (TDA / clase) ────────────────────────────────────────────────

    def p_mold_def(self, p):
        """mold_def : MOLD ID LBRACE mold_body RBRACE"""
        p[0] = NodoMold(p[2], p[4], linea=p.lineno(1))

    def p_mold_body_multi(self, p):
        """mold_body : mold_body mold_member"""
        p[0] = p[1] + [p[2]]

    def p_mold_body_empty(self, p):
        """mold_body : empty"""
        p[0] = []

    def p_mold_member(self, p):
        """mold_member : let_stmt
                       | func_def"""
        p[0] = p[1]

    # ── if / otherwise ────────────────────────────────────────────────────

    def p_if_simple(self, p):
        """if_stmt : IF expr block"""
        p[0] = NodoSi(p[2], p[3], linea=p.lineno(1))

    def p_if_otherwise(self, p):
        """if_stmt : IF expr block OTHERWISE block"""
        p[0] = NodoSi(p[2], p[3], sino=p[5], linea=p.lineno(1))

    # ── asLongAs (while) ──────────────────────────────────────────────────

    def p_while(self, p):
        """while_stmt : ASLONGAS expr block"""
        p[0] = NodoMientras(p[2], p[3], linea=p.lineno(1))

    # ── for ───────────────────────────────────────────────────────────────

    def p_for(self, p):
        """for_stmt : FOR LPAREN for_init COMMA expr COMMA for_update RPAREN block"""
        p[0] = NodoPara(p[3], p[5], p[7], p[9], linea=p.lineno(1))

    # for_init: declaración let simple, expresión, o vacío
    def p_for_init_let(self, p):
        """for_init : LET ID COLON type_annot ASSIGN expr"""
        p[0] = NodoDeclaracion(p[2], p[4], valor=p[6], linea=p.lineno(1))

    # for_update: set simple, expresión, o vacío
    def p_for_update_set_assign(self, p):
        """for_update : SET lvalue ASSIGN expr"""
        p[0] = NodoReasignacion(p[2], '=', p[4], linea=p.lineno(1))

    def p_for_update_set_pluseq(self, p):
        """for_update : SET lvalue SWEET_PLUS expr"""
        p[0] = NodoReasignacion(p[2], '+=', p[4], linea=p.lineno(1))

    def p_for_update_expr(self, p):
        """for_update : expr"""
        p[0] = p[1]

    # ── Sentencias simples ────────────────────────────────────────────────

    def p_deliver_val(self, p):
        """deliver_stmt : DELIVER expr"""
        p[0] = NodoEntregar(p[2], linea=p.lineno(1))

    def p_deliver_nothing(self, p):
        """deliver_stmt : DELIVER"""
        p[0] = NodoEntregar(linea=p.lineno(1))

    def p_show(self, p):
        """show_stmt : SHOW expr"""
        p[0] = NodoMostrar(p[2], linea=p.lineno(1))

    def p_oops(self, p):
        """oops_stmt : OOPS expr"""
        p[0] = NodoOops(p[2], linea=p.lineno(1))

    def p_expr_stmt(self, p):
        """expr_stmt : expr"""
        p[0] = p[1]

    # ── Bloque ────────────────────────────────────────────────────────────

    def p_block(self, p):
        """block : LBRACE stmt_list RBRACE"""
        p[0] = NodoBloque(p[2], linea=p.lineno(1))

    # ══════════════════════════════════════════════════════════════════════
    # EXPRESIONES
    # ══════════════════════════════════════════════════════════════════════

    # Aritmética
    def p_expr_binop(self, p):
        """expr : expr PLUS   expr
                | expr MINUS  expr
                | expr TIMES  expr
                | expr DIVIDE expr
                | expr MOD    expr"""
        p[0] = NodoBinario(p[2], p[1], p[3], linea=p.lineno(2))

    # Comparación
    def p_expr_cmp(self, p):
        """expr : expr EQ  expr
                | expr NEQ expr
                | expr LT  expr
                | expr GT  expr
                | expr LEQ expr
                | expr GEQ expr"""
        p[0] = NodoBinario(p[2], p[1], p[3], linea=p.lineno(2))

    # Lógica
    def p_expr_and(self, p):
        """expr : expr AND expr"""
        p[0] = NodoBinario('and', p[1], p[3], linea=p.lineno(2))

    def p_expr_or(self, p):
        """expr : expr OR expr"""
        p[0] = NodoBinario('or', p[1], p[3], linea=p.lineno(2))

    def p_expr_xor(self, p):
        """expr : expr XOR expr"""
        p[0] = NodoBinario('xor', p[1], p[3], linea=p.lineno(2))

    def p_expr_not(self, p):
        """expr : NOT expr"""
        p[0] = NodoUnario('not', p[2], linea=p.lineno(1))

    # Negación unaria
    def p_expr_uminus(self, p):
        """expr : MINUS expr %prec UMINUS"""
        p[0] = NodoUnario('-', p[2], linea=p.lineno(1))

    # Acceso a arreglo
    def p_expr_index(self, p):
        """expr : expr LBRACKET expr RBRACKET"""
        if isinstance(p[1], NodoAccesoArreglo):
            p[1].indices.append(p[3])
            p[0] = p[1]
        else:
            p[0] = NodoAccesoArreglo(p[1], [p[3]], linea=p.lineno(2))

    # Acceso a miembro / llamada a método
    def p_expr_method_call(self, p):
        """expr : expr DOT ID LPAREN arg_list RPAREN
                | expr DOT ID LPAREN RPAREN"""
        if len(p) == 7:
            p[0] = NodoLlamada(NodoAccesoMiembro(p[1], p[3], p.lineno(2)), p[5], linea=p.lineno(2))
        else:
            p[0] = NodoLlamada(NodoAccesoMiembro(p[1], p[3], p.lineno(2)), [], linea=p.lineno(2))

    def p_expr_member(self, p):
        """expr : expr DOT ID"""
        p[0] = NodoAccesoMiembro(p[1], p[3], linea=p.lineno(2))

    # Llamada a función
    def p_expr_call_args(self, p):
        """expr : ID LPAREN arg_list RPAREN"""
        p[0] = NodoLlamada(p[1], p[3], linea=p.lineno(1))

    def p_expr_call_noargs(self, p):
        """expr : ID LPAREN RPAREN"""
        p[0] = NodoLlamada(p[1], [], linea=p.lineno(1))

    # summon
    def p_expr_summon_args(self, p):
        """expr : SUMMON ID LPAREN arg_list RPAREN"""
        p[0] = NodoSummon(p[2], p[4], linea=p.lineno(1))

    def p_expr_summon_noargs(self, p):
        """expr : SUMMON ID LPAREN RPAREN"""
        p[0] = NodoSummon(p[2], [], linea=p.lineno(1))

    # ohmy
    def p_expr_ohmy_member(self, p):
        """expr : OHMY DOT ID"""
        p[0] = NodoAccesoMiembro(NodoOhmy(p.lineno(1)), p[3], linea=p.lineno(1))

    def p_expr_ohmy(self, p):
        """expr : OHMY"""
        p[0] = NodoOhmy(linea=p.lineno(1))

    # Agrupación
    def p_expr_group(self, p):
        """expr : LPAREN expr RPAREN"""
        p[0] = p[2]

    # Literales e identificadores
    def p_expr_id(self, p):
        """expr : ID"""
        p[0] = NodoID(p[1], linea=p.lineno(1))

    def p_expr_int(self, p):
        """expr : INT_LIT"""
        p[0] = NodoEntero(p[1], linea=p.lineno(1))

    def p_expr_float(self, p):
        """expr : FLOAT_LIT"""
        p[0] = NodoFlotante(p[1], linea=p.lineno(1))

    def p_expr_string(self, p):
        """expr : STRING"""
        p[0] = NodoCadena(p[1], linea=p.lineno(1))

    def p_expr_indeed(self, p):
        """expr : INDEED"""
        p[0] = NodoBooleano(True, linea=p.lineno(1))

    def p_expr_nope(self, p):
        """expr : NOPE"""
        p[0] = NodoBooleano(False, linea=p.lineno(1))

    def p_expr_nothing(self, p):
        """expr : NOTHING"""
        p[0] = NodoNada(linea=p.lineno(1))

    # ── Lista de argumentos ───────────────────────────────────────────────

    def p_arg_list_one(self, p):
        """arg_list : expr"""
        p[0] = [p[1]]

    def p_arg_list_many(self, p):
        """arg_list : arg_list COMMA expr"""
        p[0] = p[1] + [p[3]]

    # ── Vacío ─────────────────────────────────────────────────────────────

    def p_empty(self, p):
        """empty :"""
        p[0] = None

    # ══════════════════════════════════════════════════════════════════════
    # MANEJO DE ERRORES
    # ══════════════════════════════════════════════════════════════════════

    def p_error(self, p):
        if p:
            msg = (f"Error sintáctico en línea {p.lineno}: "
                   f"token inesperado '{p.value}' (tipo: {p.type})")
            self.errors.append(msg)
            # Recuperación: descarta el token problemático y continúa
            self.parser.errok()
        else:
            self.errors.append("Error sintáctico: fin de archivo inesperado.")

    # ══════════════════════════════════════════════════════════════════════
    # INICIALIZACIÓN Y API PÚBLICA
    # ══════════════════════════════════════════════════════════════════════

    def __init__(self):
        self._lex = AnalizadorLexico()
        self.errors: list[str] = []
        self.parser = yacc.yacc(
            module=self,
            debug=False,
            write_tables=False,
        )

    def parse(self, codigo: str) -> tuple[list[str], object]:
        """
        Analiza el código fuente y devuelve (errores, ast).

        Parámetros:
            codigo  -- cadena con el código CacaoScript preprocesado.

        Retorna:
            errores -- lista de strings con mensajes de error léxico+sintáctico.
            ast     -- NodoPrograma raíz del árbol, o None si no se pudo parsear.
        """
        self.errors = []

        # Reinicializar el lexer para el parser
        self._lex.lexer.input(codigo)
        self._lex.lexer.lineno = 1

        ast = self.parser.parse(
            lexer=self._lex.lexer,
            tracking=True,
        )

        return self.errors, ast


# Programa de prueba
if __name__ == '__main__':

    a_s = AnalizadorSintactico()
 
    sample_code = '''
let n: int = 5
let a: int[n] = 1,8,4,2,10

let max: int = a[0]

for (let i: int = 1, i < n, set i += 1){
    if (max < a[i]){
        set max = a[i]
    }
}
'''

    errors, ast = a_s.parse(sample_code)
    print(errors)
    print(ast)
