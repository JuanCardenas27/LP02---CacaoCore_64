"""
analizador_semantico.py
=======================
Analizador Semántico para CacaoScript — CACAO_Core-64.
Usa yacc para validación semántica sin construir AST.
Luego anota el AST sintáctico con información semántica.

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
from .analizador_sintactico import AnalizadorSintactico


class AnalizadorSemantico:
    """
    Analizador Semántico para CacaoScript.
    
    Realiza validación semántica mediante yacc (lógica pura, sin nodos).
    Después anota el AST sintáctico con información de símbolos y tipos.
    
    Uso:
        analyzer = AnalizadorSemantico()
        errors, ast = analyzer.parse(codigo_fuente)
    """

    # ── Tokens (lista completa del lenguaje) ────────────────────────────────
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
    # GRAMÁTICA CON LÓGICA SEMÁNTICA (SIN CONSTRUCCIÓN DE NODOS)
    # ══════════════════════════════════════════════════════════════════════

    # PROGRAMA
    def p_program(self, p):
        """program : stmt_list"""
        # Simplemente ejecutar análisis semántico del programa
        pass

    def p_stmt_list_multi(self, p):
        """stmt_list : stmt_list statement"""
        pass

    def p_stmt_list_empty(self, p):
        """stmt_list : empty"""
        pass

    # SENTENCIAS
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
        pass

    # ── Declaración let
    def p_let_simple(self, p):
        """let_stmt : LET ID COLON type_annot"""
        # Validar y definir símbolo
        name = p[2]
        type_name = self._get_type_name_from_token(p[4])
        self._define_symbol(
            name,
            'variable',
            type_name,
            p.lineno(1),
            value=None
        )

    def p_let_with_val(self, p):
        """let_stmt : LET ID COLON type_annot ASSIGN initializer"""

        name = p[2]
        type_name = self._get_type_name_from_token(p[4])

        init_data = p[6]

        self._define_symbol(
            name,
            'variable',
            type_name,
            p.lineno(1),
            value=self._extract_value(init_data)
        )

    def p_let_array_1d(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET"""
        name = p[2]
        type_name = self._get_type_name_from_token(p[4])
        self._define_symbol(
            name,
            'array',
            type_name,
            p.lineno(1),
            dims=1,
            value=None
        )

    def p_let_array_1d_val(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET ASSIGN initializer"""
        name = p[2]
        type_name = self._get_type_name_from_token(p[4])
        self._define_symbol(
            name,
            'array',
            type_name,
            p.lineno(1),
            dims=1,
            value=self._extract_value(p[9])
        )

    def p_let_array_2d(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET LBRACKET expr RBRACKET"""
        name = p[2]
        type_name = self._get_type_name_from_token(p[4])
        self._define_symbol(name, 'array', type_name, p.lineno(1), dims=2)

    def p_let_array_2d_val(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET LBRACKET expr RBRACKET ASSIGN initializer"""

        name = p[2]
        type_name = self._get_type_name_from_token(p[4])

        self._define_symbol(
            name,
            'array',
            type_name,
            p.lineno(1),
            dims=2,
            value=self._extract_value(p[12])
        )

    def p_initializer_expr(self, p):
        """initializer : expr"""
        p[0] = p[1]

    def p_initializer_list(self, p):
        """initializer : value_list"""

        p[0] = p[1]

    def p_value_list_start(self, p):
        """value_list : expr COMMA expr"""

        t1 = self._extract_type(p[1])
        t2 = self._extract_type(p[3])

        if t1 != t2:

            self._emit_error(
                p.lineno(2),
                "lista con tipos incompatibles"
            )

        p[0] = {
            'type': t1,
            'value': [
                self._extract_value(p[1]),
                self._extract_value(p[3])
            ],
            'dims': 1
        }

    def p_value_list_grow(self, p):
        """value_list : value_list COMMA expr"""

        current_type = p[1]['type']
        new_type = self._extract_type(p[3])

        if current_type != new_type:

            self._emit_error(
                p.lineno(2),
                "lista con tipos incompatibles"
            )

        values = list(p[1]['value'])

        values.append(
            self._extract_value(p[3])
        )

        p[0] = {
            'type': current_type,
            'value': values,
            'dims': 1
        }

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

    # ── Reasignación set
    def p_set_assign(self, p):
        """set_stmt : SET lvalue ASSIGN expr"""

        lvalue = p[2]
        expr_data = p[4]

        self._validate_assignment(
            p.lineno(1),
            lvalue,
            expr_data
        )

        if isinstance(lvalue, str):

            sym = self._resolve_symbol(lvalue)

            if sym is not None:
                sym['value'] = self._extract_value(expr_data)

    def p_set_pluseq(self, p):
        """set_stmt : SET lvalue SWEET_PLUS expr"""

        lvalue = p[2]
        expr_data = p[4]

        self._validate_assignment(
            p.lineno(1),
            lvalue,
            expr_data
        )

        # No calculamos nuevo valor todavía
        # porque no queremos evaluación parcial agresiva

        if isinstance(lvalue, str):

            sym = self._resolve_symbol(lvalue)

            if sym is not None:
                sym['value'] = None

    # ── Lvalue
    def p_lvalue_id(self, p):
        """lvalue : ID"""
        p[0] = p[1]

    def p_lvalue_ohmy(self, p):
        """lvalue : OHMY"""
        pass

    def p_lvalue_array_1d(self, p):
        """lvalue : lvalue LBRACKET expr RBRACKET"""
        index_type = self._extract_type(p[3])

        if index_type != 'int':

            self._emit_error(
                p.lineno(2),
                "el índice de array debe ser int"
            )
        p[0] = {
            'kind': 'array_access',
            'target': p[1]
        }

    def p_lvalue_member(self, p):
        """lvalue : lvalue DOT ID"""

        p[0] = {
            'kind': 'member_access',
            'target': p[1],
            'member': p[3]
        }

    # ── Función
    def p_func_def(self, p):
        """func_def : FUNC ID LPAREN enter_function_scope param_list RPAREN block"""

        name = p[2]

        self._define_symbol(
            name,
            'function',
            None,
            p.lineno(1),
            value=None
        )

    def p_enter_function_scope(self, p):
        """enter_function_scope :"""
        self._enter_scope('function')

    def p_func_def_no_params(self, p):
        """func_def : FUNC ID LPAREN enter_function_scope RPAREN block"""

        name = p[2]

        self._define_symbol(
            name,
            'function',
            None,
            p.lineno(1),
            value=None
        )

    def p_param_list_one(self, p):
        """param_list : param"""
        pass

    def p_param_list_many(self, p):
        """param_list : param_list COMMA param"""
        pass

    def p_param(self, p):
        """param : ID COLON type_annot"""
        name = p[1]
        type_name = p[3]
        self._define_symbol(
            name,
            'parameter',
            type_name,
            p.lineno(1),
            value=None
        )

    # ── Mold
    def p_mold_def(self, p):
        """mold_def : MOLD ID LBRACE enter_mold_scope mold_body RBRACE"""

        name = p[2]

        self._define_symbol(
            name,
            'mold',
            name,
            p.lineno(1)
        )

        self.current_mold = None

    def p_enter_mold_scope(self, p):
        """enter_mold_scope :"""
        
        mold_name = p[-2]

        self.current_mold = mold_name

        self.molds[mold_name] = {
            'fields': {},
            'methods': {}
        }

        self._enter_scope('mold')

    def p_mold_body_multi(self, p):
        """mold_body : mold_body mold_member"""
        pass

    def p_mold_body_empty(self, p):
        """mold_body : empty"""
        pass

    def p_mold_member(self, p):
        """mold_member : let_stmt
                       | func_def"""
        pass

    # ── if / otherwise
    def p_if_simple(self, p):
        """if_stmt : IF expr enter_if_scope block"""
        pass

    def p_enter_if_scope(self, p):
        """enter_if_scope :"""
        self._enter_scope('if')

    def p_if_otherwise(self, p):
        """if_stmt : IF expr enter_if_scope block OTHERWISE enter_else_scope block"""
        pass

    def p_enter_else_scope(self, p):
        """enter_else_scope :"""
        self._enter_scope('else')

    # ── asLongAs (while)
    def p_while(self, p):
        """while_stmt : ASLONGAS expr enter_while_scope block"""
        pass
    
    def p_enter_while_scope(self, p):
        """enter_while_scope :"""
        self._enter_scope('while')

    # ── for
    def p_for(self, p):
        """for_stmt : FOR LPAREN enter_for_scope for_init COMMA expr COMMA for_update RPAREN block"""
        pass

    def p_enter_for_scope(self, p):
        """enter_for_scope :"""
        self._enter_scope('for')

    def p_for_init_let(self, p):
        """for_init : LET ID COLON type_annot ASSIGN expr"""
        name = p[2]
        type_name = self._get_type_name_from_token(p[4])
        self._define_symbol(
            name,
            'variable',
            type_name,
            p.lineno(1),
            value=self._extract_value(p[6])
        )

    def p_for_update_set_assign(self, p):
        """for_update : SET lvalue ASSIGN expr"""
        pass

    def p_for_update_set_pluseq(self, p):
        """for_update : SET lvalue SWEET_PLUS expr"""
        pass

    def p_for_update_expr(self, p):
        """for_update : expr"""
        pass

    # ── Sentencias simples
    def p_deliver_val(self, p):
        """deliver_stmt : DELIVER expr"""
        pass

    def p_deliver_nothing(self, p):
        """deliver_stmt : DELIVER"""
        pass

    def p_show(self, p):
        """show_stmt : SHOW expr"""
        pass

    def p_oops(self, p):
        """oops_stmt : OOPS expr"""
        pass

    def p_expr_stmt(self, p):
        """expr_stmt : expr"""
        pass

    # ── Bloque
    def p_block(self, p):
        """block : LBRACE stmt_list RBRACE"""
        self._leave_scope()

    # EXPRESIONES
    def p_expr_binop(self, p):
        """expr : expr PLUS   expr
                | expr MINUS  expr
                | expr TIMES  expr
                | expr DIVIDE expr
                | expr MOD    expr"""

        left_type = self._extract_type(p[1])
        right_type = self._extract_type(p[3])

        result_type = 'unknown'

        numeric = {'int', 'float'}

        if left_type not in numeric or right_type not in numeric:
            self._emit_error(
                p.lineno(2),
                "operación aritmética inválida"
            )

        if left_type == 'float' or right_type == 'float':
            result_type = 'float'

        elif left_type == 'int' and right_type == 'int':
            result_type = 'int'

        p[0] = self._make_expr_data(
            result_type,
            None
        )

    def p_expr_cmp(self, p):
        """expr : expr EQ  expr
                | expr NEQ expr
                | expr LT  expr
                | expr GT  expr
                | expr LEQ expr
                | expr GEQ expr"""

        left = self._extract_type(p[1])
        right = self._extract_type(p[3])

        compatible = (
            left == right or
            (left == 'int' and right == 'float') or
            (left == 'float' and right == 'int')
        )

        if not compatible:

            self._emit_error(
                p.lineno(2),
                "comparación entre tipos incompatibles"
            )

        p[0] = self._make_expr_data(
            'bool',
            None
        )

    def p_expr_and(self, p):
        """expr : expr AND expr"""

        left = self._extract_type(p[1])
        right = self._extract_type(p[3])

        if left != 'bool' or right != 'bool':

            self._emit_error(
                p.lineno(2),
                "operación lógica requiere bool"
            )

        p[0] = self._make_expr_data(
            'bool',
            None
        )

    def p_expr_or(self, p):
        """expr : expr OR expr"""
        
        left = self._extract_type(p[1])
        right = self._extract_type(p[3])

        if left != 'bool' or right != 'bool':

            self._emit_error(
                p.lineno(2),
                "operación lógica requiere bool"
            )

        p[0] = self._make_expr_data(
            'bool',
            None
        )

    def p_expr_xor(self, p):
        """expr : expr XOR expr"""
        
        left = self._extract_type(p[1])
        right = self._extract_type(p[3])

        if left != 'bool' or right != 'bool':

            self._emit_error(
                p.lineno(2),
                "operación lógica requiere bool"
            )

        p[0] = self._make_expr_data(
            'bool',
            None
        )

    def p_expr_not(self, p):
        """expr : NOT expr"""

        expr_type = self._extract_type(p[2])

        if expr_type != 'bool':

            self._emit_error(
                p.lineno(1),
                "operación lógica requiere bool"
            )

        p[0] = self._make_expr_data(
            'bool',
            None
        )

    def p_expr_uminus(self, p):
        """expr : MINUS expr %prec UMINUS"""
        p[0] = self._make_expr_data(
            self._extract_type(p[2]),
            None
        )

    def p_expr_index(self, p):
        """expr : expr LBRACKET expr RBRACKET"""

        target = p[1]
        index = p[3]

        index_type = self._extract_type(index)

        if index_type != 'int':
            self._emit_error(
                p.lineno(2),
                "el índice de array debe ser int"
            )

        target_type = self._extract_type(target)

        if isinstance(target, dict):

            dims = target.get('dims', 0)

            if dims <= 0:
                self._emit_error(
                    p.lineno(2),
                    "el símbolo no es indexable"
                )

            p[0] = self._make_expr_data(
                target_type,
                None,
                dims=max(dims - 1, 0)
            )

        else:

            p[0] = self._make_expr_data(
                'unknown',
                None
            )

    def p_expr_method_call(self, p):
        """expr : expr DOT ID LPAREN arg_list RPAREN
                | expr DOT ID LPAREN RPAREN"""
        p[0] = self._make_expr_data(
            'unknown',
            None
        )

    def p_expr_member(self, p):
        """expr : expr DOT ID"""

        left = p[1]
        member = p[3]

        left_type = self._extract_type(left)

        mold = self.molds.get(left_type)

        if mold is None:

            self._emit_error(
                p.lineno(2),
                f"'{left_type}' no es un mold"
            )

            p[0] = self._make_expr_data('unknown')
            return

        field = mold['fields'].get(member)

        if field is None:

            self._emit_error(
                p.lineno(2),
                f"el mold '{left_type}' no tiene miembro '{member}'"
            )

            p[0] = self._make_expr_data('unknown')
            return

        p[0] = self._make_expr_data(
            field['type'],
            None,
            field.get('dims', 0)
        )

    def p_expr_call_args(self, p):
        """expr : ID LPAREN arg_list RPAREN"""
        # Validar que función existe
        name = p[1]
        sym = self._resolve_symbol(name)
        if sym is None:

            self._emit_error(
                p.lineno(1),
                f"función '{name}' no declarada"
            )

            p[0] = self._make_expr_data('unknown')
            return
        p[0] = self._make_expr_data(
            sym.get('type', 'unknown'),
            sym.get('value'),
            sym.get('dims', 0)
        )

    def p_expr_call_noargs(self, p):
        """expr : ID LPAREN RPAREN"""
        name = p[1]
        sym = self._resolve_symbol(name)
        if sym is None:

            self._emit_error(
                p.lineno(1),
                f"función '{name}' no declarada"
            )

            p[0] = self._make_expr_data('unknown')
            return
        p[0] = self._make_expr_data(
            sym.get('type', 'unknown'),
            sym.get('value'),
            sym.get('dims', 0)
        )

    def p_expr_summon_args(self, p):
        """expr : SUMMON ID LPAREN arg_list RPAREN"""
        mold_name = p[2]

        sym = self._resolve_symbol(mold_name)

        if sym is None or sym.get('kind') != 'mold':
            self._emit_error(
                p.lineno(1),
                f"mold '{mold_name}' no declarado"
            )

        p[0] = self._make_expr_data(
            p[2],
            None
        )

    def p_expr_summon_noargs(self, p):
        """expr : SUMMON ID LPAREN RPAREN"""
        mold_name = p[2]

        sym = self._resolve_symbol(mold_name)

        if sym is None or sym.get('kind') != 'mold':
            self._emit_error(
                p.lineno(1),
                f"mold '{mold_name}' no declarado"
            )
            
        p[0] = self._make_expr_data(
            p[2],
            None
        )

    def p_expr_ohmy_member(self, p):
        """expr : OHMY DOT ID"""
        p[0] = self._make_expr_data(
            'unknown',
            None
        )

    def p_expr_ohmy(self, p):
        """expr : OHMY"""
        p[0] = self._make_expr_data(
            'unknown',
            None
        )

    def p_expr_group(self, p):
        """expr : LPAREN expr RPAREN"""
        p[0] = p[2]

    def p_expr_id(self, p):
        """expr : ID"""

        name = p[1]

        sym = self._resolve_symbol(name)

        if sym is None:

            self._emit_error(
                p.lineno(1),
                f"símbolo '{name}' no declarado"
            )

            p[0] = self._make_expr_data('unknown')
            return

        p[0] = self._make_expr_data(
            sym.get('type', 'unknown'),
            sym.get('value'),
            sym.get('dims', 0)
        )

    def p_expr_int(self, p):
        """expr : INT_LIT"""

        p[0] = self._make_expr_data(
            'int',
            p[1]
        )

    def p_expr_float(self, p):
        """expr : FLOAT_LIT"""

        p[0] = self._make_expr_data(
            'float',
            p[1]
        )

    def p_expr_string(self, p):
        """expr : STRING"""

        p[0] = self._make_expr_data(
            'text',
            p[1]
        )

    def p_expr_indeed(self, p):
        """expr : INDEED"""

        p[0] = self._make_expr_data(
            'bool',
            True
        )

    def p_expr_nope(self, p):
        """expr : NOPE"""

        p[0] = self._make_expr_data(
            'bool',
            False
        )

    def p_expr_nothing(self, p):
        """expr : NOTHING"""

        p[0] = self._make_expr_data(
            'void',
            None
        )

    def p_arg_list_one(self, p):
        """arg_list : expr"""
        pass

    def p_arg_list_many(self, p):
        """arg_list : arg_list COMMA expr"""
        pass

    # ── Vacío
    def p_empty(self, p):
        """empty :"""
        pass

    # MANEJO DE ERRORES
    def p_error(self, p):
        if p:
            msg = (f"Error sintáctico en línea {p.lineno}: "
                   f"token inesperado '{p.value}' (tipo: {p.type})")
            self.errors.append(msg)
            self.parser.errok()
        else:
            self.errors.append("Error sintáctico: fin de archivo inesperado.")

    # ══════════════════════════════════════════════════════════════════════
    # INICIALIZACIÓN Y API PÚBLICA
    # ══════════════════════════════════════════════════════════════════════

    def __init__(self):
        self._lex = AnalizadorLexico()
        self._syntactic = AnalizadorSintactico()
        self.errors: list[str] = []
        self.scopes: list[dict] = [{}]  # Alcances
        self.scope_names: list[str] = ['global']
        # Persistir definiciones para poder anotar el AST después
        self.defined_symbols: list[dict] = []
        # Tabla semántica: parte de la tabla del lexer y se enriquece en yacc
        self.semantic_symbol_table: dict[str, dict] = {}
        self.molds = {}
        self.current_mold = None
        self.parser = yacc.yacc(
            module=self,
            debug=False,
            write_tables=False,
        )

    def parse(self, codigo: str) -> tuple[list[str], object]:
        """
        Analiza y valida semánticamente el código.
        
        Parámetros:
            codigo  -- cadena con el código CacaoScript.
        
        Retorna:
            errores -- lista de mensajes de error semánticos.
            ast     -- AST anotado con información semántica (por ahora devuelve sintáctico).
        """
        self.errors = []
        self._reset_semantic_state()

        # Paso 0: ejecutar lexer para obtener la tabla base real
        # y usarla como base de la tabla semántica enriquecida.
        self._lex.analize(codigo)
        self.semantic_symbol_table = {
            lexeme: {
                'lexeme': row.get('lexeme'),
                'length': row.get('length'),
                'lines': list(row.get('lines', [])),
                'kind': row.get('kind'),
                'type': row.get('type'),
                'value': row.get('value'),
                'scope': row.get('scope'),
            }
            for lexeme, row in self._lex.symbol_table.items()
        }

        # Paso 1: Parsear con yacc para ejecutar lógica semántica
        self._lex.lexer.input(codigo)
        self._lex.lexer.lineno = 1

        self.parser.parse(
            lexer=self._lex.lexer,
            tracking=True,
        )

        # Paso 2: Si no hay errores semánticos, obtener el AST sintáctico
        if not self.errors:
            errors_syntactic, ast = self._syntactic.parse(codigo)
            # Anotar AST sintáctico con la información recolectada
            try:
                if ast is not None:
                    self._annotate_ast(ast)
            except Exception:
                # No interrumpir por anotación: devolver ast aunque la anotación falle
                pass
            return errors_syntactic + self.errors, ast
        else:
            return self.errors, None

    def _make_expr_data(
        self,
        type_name='unknown',
        value=None,
        dims=0
    ):
        return {
            'type': type_name,
            'value': value,
            'dims': dims
        }

    def _extract_type(self, expr_data):
        if isinstance(expr_data, dict):
            return expr_data.get('type')
        return expr_data

    def _extract_value(self, expr_data):
        if isinstance(expr_data, dict):
            return expr_data.get('value')
        return None
    
    def _extract_dims(self, expr_data):
        if isinstance(expr_data, dict):
            return expr_data.get('dims', 0)
        return 0
    
    def _resolve_lvalue_type(self, lvalue, line):

        if isinstance(lvalue, str):

            sym = self._resolve_symbol(lvalue)

            if sym is None:
                return None

            return {
                'type': sym.get('type'),
                'dims': sym.get('dims', 0)
            }

        if isinstance(lvalue, dict):

            kind = lvalue.get('kind')

            if kind == 'member_access':

                target_info = self._resolve_lvalue_type(
                    lvalue['target'],
                    line
                )

                if target_info is None:
                    return None

                mold = self.molds.get(target_info['type'])

                if mold is None:
                    return None

                field = mold['fields'].get(
                    lvalue['member']
                )

                if field is None:

                    self._emit_error(
                        line,
                        f"miembro '{lvalue['member']}' no existe"
                    )

                    return None

                return field

            elif kind == 'array_access':

                target_info = self._resolve_lvalue_type(
                    lvalue['target'],
                    line
                )

                if target_info is None:
                    return None

                dims = target_info.get('dims', 0)

                return {
                    'type': target_info['type'],
                    'dims': max(dims - 1, 0)
                }

        return None

    def _reset_semantic_state(self):
        """Reinicializar estado semántico."""
        self.scopes = [{}]
        self.scope_names = ['global']
        self.defined_symbols = []
        self.semantic_symbol_table = {}

    def _emit_error(self, line: int, message: str):
        """Emitir error semántico."""
        self.errors.append(f"Error semántico en línea {line}: {message}")

    def _get_type_name_from_token(self, token_value) -> str:
        """Extraer nombre de tipo de un token."""
        if isinstance(token_value, str):
            return token_value
        return str(token_value)

    def _enter_scope(self, kind: str):
        """Entrar a un nuevo alcance."""
        self.scopes.append({})
        self.scope_names.append(kind)

    def _leave_scope(self):
        """Salir del alcance actual."""
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.scope_names.pop()

    def _define_symbol(
        self,
        name: str,
        kind: str,
        type_name: str | None,
        line: int,
        dims: int = 0,
        value=None
    ):
        """Definir un símbolo en el alcance actual."""
        current_scope = self.scopes[-1]
        if name in current_scope:
            scope_name = self.scope_names[-1] if self.scope_names else 'unknown'
            self._emit_error(line, f"símbolo '{name}' ya fue definido en '{scope_name}'")
            return False
        entry = {
            'name': name,
            'kind': kind,
            'type': type_name,
            'value': value,
            'line': line,
            'dims': dims,
            'scope': self.scope_names[-1] if self.scope_names else 'unknown',
        }
        current_scope[name] = entry
        self.defined_symbols.append(entry.copy())
        self._enrich_lexer_symbol_entry(name, entry)
        if self.current_mold is not None:

            mold_data = self.molds[self.current_mold]

            if kind in ('variable', 'array'):

                mold_data['fields'][name] = {
                    'type': type_name,
                    'dims': dims
                }

            elif kind == 'function':

                mold_data['methods'][name] = {
                    'type': type_name
                }
        return True

    def _enrich_lexer_symbol_entry(self, name: str, sem_entry: dict):
        """Enriquecer la entrada base del lexer con metadatos semánticos de yacc."""
        row = self.semantic_symbol_table.get(name)
        if row is None:
            # Fallback: si por alguna razón no existe en lexer, crear forma compatible
            row = {
                'lexeme': name,
                'length': len(name),
                'lines': [sem_entry.get('line')],
                'kind': None,
                'type': None,
                'value': None,
                'scope': None,
            }
            self.semantic_symbol_table[name] = row

        row['kind'] = sem_entry.get('kind')
        row['type'] = sem_entry.get('type')
        row['value'] = sem_entry.get('value')
        row['scope'] = sem_entry.get('scope')
        line = sem_entry.get('line')
        if line is not None and line not in row.get('lines', []):
            row.setdefault('lines', []).append(line)

    def _resolve_symbol(self, name: str) -> dict | None:
        """Resolver un símbolo buscando en alcances de adentro hacia afuera."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def _find_symbol_for_name(self, name: str, use_line: int) -> dict | None:
        """Buscar la definición más cercana por línea (<= use_line) para un nombre.
        Usa `defined_symbols` para no depender de scopes temporales.
        """
        candidates = [s for s in self.defined_symbols if s.get('name') == name and s.get('line', 0) <= use_line]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.get('line', 0))

    def _validate_assignment(self, line: int, lvalue, expr_data):
        """
        Validar compatibilidad entre un lvalue y una expresión.
        """

        target_info = self._resolve_lvalue_type(
            lvalue,
            line
        )

        if target_info is None:
            return False

        declared_type = target_info.get('type')
        declared_dims = target_info.get('dims', 0)

        expr_type = self._extract_type(expr_data)
        expr_dims = self._extract_dims(expr_data)

        # ── Validar dimensiones
        if declared_dims != expr_dims:

            self._emit_error(
                line,
                f"dimensiones incompatibles: "
                f"se esperaba {declared_dims}D "
                f"y se recibió {expr_dims}D"
            )

            return False

        # ── Tipos desconocidos
        if declared_type in (None, 'unknown'):
            return True

        if expr_type in (None, 'unknown'):
            return True

        # ── Promoción int -> float
        if declared_type == 'float' and expr_type == 'int':
            return True

        # ── Compatibilidad exacta
        if declared_type != expr_type:

            self._emit_error(
                line,
                f"asignación incompatible: "
                f"no se puede asignar "
                f"'{expr_type}' a '{declared_type}'"
            )

            return False

        return True

    def _annotate_ast(self, node):
        """Recorrido del AST para agregar metadatos semánticos básicos.
        Añade `symbol` y `tipo` en nodos relevantes.
        """
        from .ast_nodos import Nodo, NodoID, NodoDeclaracion, NodoEntero, NodoFlotante, NodoCadena, NodoBooleano, NodoParametro

        if node is None:
            return
        if isinstance(node, (list, tuple)):
            for n in node:
                self._annotate_ast(n)
            return
        if not isinstance(node, Nodo):
            return

        # Declaración: buscar símbolo definido exactamente en la línea
        if isinstance(node, NodoDeclaracion):
            try:
                name = node.nombre if isinstance(node.nombre, str) else getattr(node.nombre, 'nombre', None)
            except Exception:
                name = None
            if name:
                sym = next((s for s in self.defined_symbols if s.get('name') == name and s.get('line') == node.linea), None)
                if sym:
                    node.symbol = sym
                    node.tipo_decl = sym.get('type')

        # Parámetro
        if isinstance(node, NodoParametro):
            name = node.nombre if isinstance(node.nombre, str) else getattr(node.nombre, 'nombre', None)
            if name:
                sym = next((s for s in self.defined_symbols if s.get('name') == name and s.get('line') == node.linea), None)
                if sym:
                    node.symbol = sym
                    node.tipo_decl = sym.get('type')

        # ID: resolver por línea
        if isinstance(node, NodoID):
            name = node.nombre
            use_line = getattr(node, 'linea', 0) or 0
            sym = self._find_symbol_for_name(name, use_line)
            if sym:
                node.symbol = sym
                node.tipo = sym.get('type')

        # Literales
        if isinstance(node, NodoEntero):
            node.tipo = 'int'
        if isinstance(node, NodoFlotante):
            node.tipo = 'float'
        if isinstance(node, NodoCadena):
            node.tipo = 'text'
        if isinstance(node, NodoBooleano):
            node.tipo = 'bool'

        # Recorrer campos
        for name, child in list(node.__dict__.items()):
            if name.startswith('_'):
                continue
            if child is None:
                continue
            self._annotate_ast(child)
