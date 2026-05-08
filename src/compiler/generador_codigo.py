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
from analizador_lexico import AnalizadorLexico
from ast_nodos import (
    NodoPrograma, NodoDeclaracion, NodoReasignacion, NodoFuncion, NodoMold,
    NodoSi, NodoMientras, NodoPara, NodoEntregar, NodoMostrar, NodoOops,
    NodoBloque, NodoBinario, NodoUnario, NodoLlamada,
    NodoAccesoMiembro, NodoAccesoArreglo, NodoSummon, NodoListaValores,
    NodoID, NodoEntero, NodoFlotante, NodoCadena, NodoBooleano, NodoNada,
    NodoOhmy,
)


class GeneradorCodigo:
    """
    Parser LALR(1) para CacaoScript.

    Uso:
        parser = AnalizadorSemantico()
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

    

    # ─────────────────────────────────────────────────────────────
    # PROGRAM
    # ─────────────────────────────────────────────────────────────

    def p_program(self, p):
        """program : stmt_list"""

        final_code = []

        for stmt in p[1]:

            if isinstance(stmt, dict):
                final_code.extend(stmt.get('code', []))
        final_code.append('HLT')
        self.text = final_code

        p[0] = final_code



    # ─────────────────────────────────────────────────────────────
    # STMT LIST
    # ─────────────────────────────────────────────────────────────

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

        defecto = 0

        if p[4] == "int":
            defecto = 0
        elif p[4] == "float":
            defecto = 0.0
        elif p[4] == "text":
            defecto = ' '
        elif p[4] == "bool":
            defecto = 0

        decl = f'{p[2]} : {defecto}'

        self.data.append(decl)

        p[0] = {
            "code": [],
            "result": p[2]
        }


    def p_let_with_val(self, p):
        """let_stmt : LET ID COLON type_annot ASSIGN initializer"""

        value = p[6]

        if isinstance(value, dict):
            init_value = value["result"]
            code = value["code"]
        else:
            init_value = value
            code = []

        # string -> convertir a arreglo de chars
        if isinstance(init_value, str) and p[4] == "text":

            for i, ch in enumerate(init_value):
                self.data.append(f"{p[2]}{i} : '{ch}'")

        else:

            decl = f'{p[2]} : {init_value}'
            self.data.append(decl)

        p[0] = {
            "code": code,
            "result": p[2]
        }

    def p_let_array_1d(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET"""

        defecto = 0

        if p[4] == "int":
            defecto = 0
        elif p[4] == "float":
            defecto = 0.0
        elif p[4] == "text":
            defecto = ' '
        elif p[4] == "bool":
            defecto = 0

        length = p[6]

        if isinstance(length, dict):
            length = self.sim_table[length["result"]]["value"]

        for i in range(length):
            self.data.append(f'{p[2]}{i} : {defecto}')

        p[0] = {
            "code": [],
            "result": p[2]
        }


    def p_let_array_1d_val(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET ASSIGN initializer"""

        length = p[6]
        
        if isinstance(length, dict):
            try:
                length = self.sim_table[length["result"]]["value"]
            except KeyError:
                length = length["result"]

        values = p[9]

        for i in range(length):
            self.data.append(f'{p[2]}{i} : {values[i]['result']}')

        p[0] = {
            "code": [],
            "result": p[2]
        }


    def p_let_array_2d(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET LBRACKET expr RBRACKET"""

        defecto = 0

        if p[4] == "int":
            defecto = 0
        elif p[4] == "float":
            defecto = 0.0
        elif p[4] == "text":
            defecto = ' '
        elif p[4] == "bool":
            defecto = 0

        rows = p[6]
        cols = p[9]

        if isinstance(rows, dict):
            rows = self.sim_table[rows["result"]]["value"]

        if isinstance(cols, dict):
            cols = self.sim_table[cols["result"]]["value"]

        total = rows * cols

        for i in range(total):
            self.data.append(f'{p[2]}{i} : {defecto}')

        p[0] = {
            "code": [],
            "result": p[2]
        }


    def p_let_array_2d_val(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET LBRACKET expr RBRACKET ASSIGN initializer"""

        rows = p[6]
        cols = p[9]

        if isinstance(rows, dict):
            rows = self.sim_table[rows["result"]]["value"]

        if isinstance(cols, dict):
            cols = self.sim_table[cols["result"]]["value"]

        values = p[12]

        total = rows * cols

        for i in range(total):
            self.data.append(f'{p[2]}{i} : {values[i]}')

        p[0] = {
            "code": [],
            "result": p[2]
        }
    # Inicializador: expresión simple o lista de valores separada por comas

    def p_initializer_expr(self, p):
        """initializer : expr"""
        p[0] = p[1]

    def p_initializer_list(self, p):
        """initializer : value_list"""
        p[0] = p[1]

    def p_value_list_start(self, p):
        """value_list : expr COMMA expr"""
        p[0] = [p[1], p[3]]

    def p_value_list_grow(self, p):
        """value_list : value_list COMMA expr"""
        p[1].append(p[3])
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

    # ─────────────────────────────────────────────────────────────
    # SET
    # ─────────────────────────────────────────────────────────────

    def p_set_assign(self, p):
        """set_stmt : SET lvalue ASSIGN expr"""

        instr = []

        instr.extend(p[2]['code'])
        instr.extend(p[4]['code'])

        expr_res = self.format_operand(p[4])

        instr.append(f'MOVD [R1], {expr_res}')

        p[0] = {
            'code': instr
        }



    def p_set_pluseq(self, p):
        """set_stmt : SET lvalue SWEET_PLUS expr"""
        p[0] = NodoReasignacion(p[2], '+=', p[4], linea=p.lineno(1))

    # ── Lvalue ────────────────────────────────────────────────────────────

    # ─────────────────────────────────────────────────────────────
    # LVALUES
    # ─────────────────────────────────────────────────────────────

    def p_lvalue_id(self, p):
        """lvalue : ID"""

        p[0] = {
            'code': [f'LEA R1, {p[1]}'],
            'result': 'R1'
        }

    def p_lvalue_ohmy(self, p):
        """lvalue : OHMY"""
        p[0] = NodoOhmy(linea=p.lineno(1))

    def p_lvalue_array_1d(self, p):
        """lvalue : lvalue LBRACKET expr RBRACKET"""

        instr = []

        instr.extend(p[1]['code'])
        instr.extend(p[3]['code'])

        index = self.format_operand(p[3])

        instr.extend([
            f'MOV R2, {index}',
            'MUL R2, 8',
            'ADD R1, R2'
        ])

        p[0] = {
            'code': instr,
            'result': 'R1'
        }


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

    # ─────────────────────────────────────────────────────────────
    # IF
    # ─────────────────────────────────────────────────────────────

    def p_if_simple(self, p):
        """if_stmt : IF expr block"""

        else_label = f"LFALSE{self.if_counter}"
        end_label  = f"LEND{self.if_counter}"

        self.if_counter += 1

        cond_code = p[2]['code']
        cond_res  = self.format_operand(p[2])

        block_code = p[3]['code']

        instr = []

        instr.extend(cond_code)

        instr.extend([
            f'CMP {cond_res}, 0',
            f'JE {else_label}'
        ])

        instr.extend(block_code)

        instr.extend([
            f'JMP {end_label}',
            f'{else_label}:',
            f'{end_label}:'
        ])

        p[0] = {
            'code': instr
        }



    
    def p_if_otherwise(self, p):
        """if_stmt : IF expr block OTHERWISE block"""

        else_label = f"LELSE{self.else_counter}"
        end_label  = f"LEND{self.if_counter}"

        self.else_counter += 1
        self.if_counter += 1

        cond_code = p[2]['code']
        cond_res  = self.format_operand(p[2])

        then_code = p[3]['code']
        else_code = p[5]['code']

        instr = []

        instr.extend(cond_code)

        instr.extend([
            f'CMP {cond_res}, 0',
            f'JE {else_label}'
        ])

        instr.extend(then_code)

        instr.extend([
            f'JMP {end_label}',
            f'{else_label}:'
        ])

        instr.extend(else_code)

        instr.append(f'{end_label}:')

        p[0] = {
            'code': instr
        }

    # ── asLongAs (while) ──────────────────────────────────────────────────

    def p_while(self, p):
        """while_stmt : ASLONGAS expr block"""

        start_label = f"LWHILE_START{self.while_counter}"
        end_label   = f"LWHILE_END{self.while_counter}"

        self.while_counter += 1

        cond_code = p[2]["code"]
        cond_reg  = self.format_operand(p[2])

        body_code = p[3]["code"]

        code = []

        code.append(f"{start_label}:")

        code.extend(cond_code)

        code.append(f"CMP {cond_reg}, 0")
        code.append(f"JE {end_label}")

        code.extend(body_code)

        code.append(f"JMP {start_label}")

        code.append(f"{end_label}:")

        p[0] = {
            "code": code
        }
    # ── for ───────────────────────────────────────────────────────────────

    def p_for(self, p):
        """for_stmt : FOR LPAREN for_init COMMA expr COMMA for_update RPAREN block"""

        start_label = f"LFOR_START{self.for_counter}"
        end_label   = f"LFOR_END{self.for_counter}"

        self.for_counter += 1

        init_code = p[3]["code"]

        cond_code = p[5]["code"]
        cond_reg  = self.format_operand(p[5])

        update_code = p[7]["code"]

        body_code = p[9]["code"]

        code = []

        code.extend(init_code)

        code.append(f"{start_label}:")

        code.extend(cond_code)

        code.append(f"CMP {cond_reg}, 0")
        code.append(f"JE {end_label}")

        code.extend(body_code)

        code.extend(update_code)

        code.append(f"JMP {start_label}")

        code.append(f"{end_label}:")

        p[0] = {
            "code": code
        }
    # for_init: declaración let simple, expresión, o vacío
    def p_for_init_let(self, p):
        """for_init : LET ID COLON type_annot ASSIGN expr"""

        value = p[6]

        if isinstance(value, dict):
            init_value = value["result"]
            code = value["code"]
        else:
            init_value = value
            code = []

        self.data.append(f"{p[2]} : 0")

        code.append(f"MOVD [{p[2]}], {init_value}")

        p[0] = {
            "code": code,
            "result": p[2]
        }

    # for_update: set simple, expresión, o vacío
    def p_for_update_set_assign(self, p):
        """for_update : SET lvalue ASSIGN expr"""

        lvalue_code = p[2]["code"]
        expr_code   = p[4]["code"]
        expr_result = p[4]["result"]

        code = []

        code.extend(lvalue_code)
        code.extend(expr_code)

        code.append(f"MOVD [R1], {expr_result}")

        p[0] = {
            "code": code,
            "result": None
        }

    def p_for_update_set_pluseq(self, p):
        """for_update : SET lvalue SWEET_PLUS expr"""

        lvalue_code = p[2]["code"]
        expr_code   = p[4]["code"]
        expr_result = p[4]["result"]

        code = []

        code.extend(lvalue_code)
        code.extend(expr_code)

        code.extend([
            "MOV R6, [R1]",
            f"ADD R6, {expr_result}",
            "MOVD [R1], R6"
        ])

        p[0] = {
            "code": code,
            "result": None
        }

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

    # ─────────────────────────────────────────────────────────────
    # BLOCK
    # ─────────────────────────────────────────────────────────────

    def p_block(self, p):
        """block : LBRACE stmt_list RBRACE"""

        code = []

        for stmt in p[2]:

            if isinstance(stmt, dict):
                code.extend(stmt.get('code', []))

        p[0] = {
            'code': code
        }

    # ══════════════════════════════════════════════════════════════════════
    # EXPRESIONES
    # ══════════════════════════════════════════════════════════════════════
    
    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────

    def format_operand(self, value):

        if isinstance(value, dict):
            return value['result']

        if isinstance(value, (int, float)):
            return str(value)

        if isinstance(value, str) and value.startswith("R"):
            return value

        return f'[{value}]'
    
    # ─────────────────────────────────────────────────────────────
    # ARITHMETIC
    # ─────────────────────────────────────────────────────────────

    def p_expr_binop(self, p):
        """expr : expr PLUS expr
                | expr MINUS expr
                | expr TIMES expr
                | expr DIVIDE expr
                | expr MOD expr"""

        left_code  = p[1]['code']
        right_code = p[3]['code']

        left  = self.format_operand(p[1])
        right = self.format_operand(p[3])

        instr = []

        instr.extend(left_code)
        instr.extend(right_code)

        instr.append(f'MOV R3, {left}')

        is_float = (
            isinstance(p[1]['result'], float) or
            isinstance(p[3]['result'], float)
        )

        if p[2] == '+':

            if is_float:
                instr.append(f'FPADD R3, {right}')
            else:
                instr.append(f'ADD R3, {right}')

        elif p[2] == '-':

            if is_float:
                instr.append(f'FPSUB R3, {right}')
            else:
                instr.append(f'SUB R3, {right}')

        elif p[2] == '*':

            if is_float:
                instr.append(f'FPMUL R3, {right}')
            else:
                instr.append(f'MUL R3, {right}')

        elif p[2] == '/':

            if is_float:
                instr.append(f'FPDIV R3, {right}')
            else:
                instr.append(f'DIV R3, {right}')

        elif p[2] == '%':

            if is_float:
                instr.append(f'FPMOD R3, {right}')
            else:
                instr.append(f'MOD R3, {right}')

        p[0] = {
            'code': instr,
            'result': 'R3'
        }



    # ─────────────────────────────────────────────────────────────
    # COMPARISONS
    # ─────────────────────────────────────────────────────────────

    def p_expr_cmp(self, p):
        """expr : expr EQ expr
                | expr NEQ expr
                | expr LT expr
                | expr GT expr
                | expr LEQ expr
                | expr GEQ expr"""

        left_code  = p[1]['code']
        right_code = p[3]['code']

        left  = self.format_operand(p[1])
        right = self.format_operand(p[3])

        true_label = f"LTRUE{self.cmp_label_count}"
        end_label  = f"LEND{self.cmp_label_count}"

        self.cmp_label_count += 1

        instr = []

        instr.extend(left_code)
        instr.extend(right_code)

        instr.extend([
            f'MOV R3, {left}',
            f'CMP R3, {right}',
        ])

        if p[2] == '==':
            instr.append(f'JE {true_label}')

        elif p[2] == '!=':
            instr.append(f'JNE {true_label}')

        elif p[2] == '<':
            instr.append(f'JL {true_label}')

        elif p[2] == '>':
            instr.append(f'JG {true_label}')

        elif p[2] == '<=':
            instr.append(f'JLE {true_label}')

        elif p[2] == '>=':
            instr.append(f'JGE {true_label}')

        instr.extend([
            'MOV R5, 0',
            f'JMP {end_label}',
            f'{true_label}:',
            'MOV R5, 1',
            f'{end_label}:'
        ])

        p[0] = {
            'code': instr,
            'result': 'R5'
        }

    # ─────────────────────────────────────────────────────────────
    # LOGICAL
    # ─────────────────────────────────────────────────────────────

    def p_expr_and(self, p):
        """expr : expr AND expr"""

        left_code  = p[1]['code']
        right_code = p[3]['code']

        left  = self.format_operand(p[1])
        right = self.format_operand(p[3])

        instr = []

        instr.extend(left_code)
        instr.extend(right_code)

        instr.extend([
            f'MOV R4, {left}',
            f'AND R4, {right}'
        ])

        p[0] = {
            'code': instr,
            'result': 'R4'
        }


    def p_expr_or(self, p):
        """expr : expr OR expr"""

        left_code  = p[1]['code']
        right_code = p[3]['code']

        left  = self.format_operand(p[1])
        right = self.format_operand(p[3])

        instr = []

        instr.extend(left_code)
        instr.extend(right_code)

        instr.extend([
            f'MOV R4, {left}',
            f'OR R4, {right}'
        ])

        p[0] = {
            'code': instr,
            'result': 'R4'
        }


    def p_expr_xor(self, p):
        """expr : expr XOR expr"""

        left_code  = p[1]['code']
        right_code = p[3]['code']

        left  = self.format_operand(p[1])
        right = self.format_operand(p[3])

        instr = []

        instr.extend(left_code)
        instr.extend(right_code)

        instr.extend([
            f'MOV R4, {left}',
            f'XOR R4, {right}'
        ])

        p[0] = {
            'code': instr,
            'result': 'R4'
        }


    def p_expr_not(self, p):
        """expr : NOT expr"""

        value = self.format_operand(p[2])

        instr = []

        instr.extend(p[2]['code'])

        instr.extend([
            f'MOV R4, {value}',
            'NOT R4'
        ])

        p[0] = {
            'code': instr,
            'result': 'R4'
        }




    # ─────────────────────────────────────────────────────────────
    # UMINUS
    # ─────────────────────────────────────────────────────────────

    def p_expr_uminus(self, p):
        """expr : MINUS expr %prec UMINUS"""

        value = self.format_operand(p[2])

        instr = []

        instr.extend(p[2]['code'])

        instr.append(f'MOV R3, {value}')

        if isinstance(p[2]['result'], float):
            instr.append('FPMUL R3, -1.0')
        else:
            instr.append('MUL R3, -1')

        p[0] = {
            'code': instr,
            'result': 'R3'
        }


    # Acceso a arreglo
    def p_expr_index(self, p):
        """expr : expr LBRACKET expr RBRACKET"""

        array_expr = p[1]
        index_expr = p[3]

        code = []

        # código base arreglo
        code.extend(array_expr["code"])

        # código índice
        code.extend(index_expr["code"])

        array_name = array_expr["result"]
        index_value = self.format_operand(index_expr)

        # calcular offset
        code.append(f"MOV R1, {index_value}")
        code.append("MUL R1, 8")

        # dirección base
        code.append(f"LEA R2, {array_name}")

        # dirección final
        code.append("ADD R1, R2")

        # cargar valor
        code.append("MOV R3, [R1]")

        p[0] = {
            "code": code,
            "result": "R3"
        }

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
        p[0] = p[1]

    # Agrupación
    def p_expr_group(self, p):
        """expr : LPAREN expr RPAREN"""
        p[0] = p[2]




    # ─────────────────────────────────────────────────────────────
    # LITERALS
    # ─────────────────────────────────────────────────────────────

    def p_expr_id(self, p):
        """expr : ID"""

        p[0] = {
            'code': [],
            'result': p[1]
        }


    def p_expr_int(self, p):
        """expr : INT_LIT"""

        p[0] = {
            'code': [],
            'result': int(p[1])
        }


    def p_expr_float(self, p):
        """expr : FLOAT_LIT"""

        p[0] = {
            'code': [],
            'result': float(p[1])
        }


    def p_expr_string(self, p):
        """expr : STRING"""

        p[0] = {
            'code': [],
            'result': str(p[1])
        }


    def p_expr_indeed(self, p):
        """expr : INDEED"""

        p[0] = {
            'code': [],
            'result': 1
        }


    def p_expr_nope(self, p):
        """expr : NOPE"""

        p[0] = {
            'code': [],
            'result': 0
        }


    def p_expr_nothing(self, p):
        """expr : NOTHING"""
        p[0] = {
            'code': [],
            'result': -0.0
        }

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
        self.text = []
        self.data = []
        self.cmp_label_count = 0
        self.else_counter = 0
        self.if_counter = 0
        self.while_counter = 0
        self.for_counter = 0

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
        _, self.sim_table, _, self.num_table = self._lex.analize(codigo)
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

    a_s = GeneradorCodigo()
 
    sample_code = '''
    let n: int = 5
    let a: int[5] = 1,8,4,2,10

    let max: int = 0

    set max = a[0]

    for (let i: int = 1, i < n, set i += 1){
        if (max < a[i]){
            set max = a[i]
        }
    }

'''

    errors, ast = a_s.parse(sample_code)
    print(errors)
    print(a_s.data)
    print(a_s.text)
