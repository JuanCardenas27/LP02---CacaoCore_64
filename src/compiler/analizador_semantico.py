"""
analizador_semantico.py
=======================
Analizador Semántico para Choco — CACAO_Core-64.
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

let_stmt        ::= 'let' ID ':' type_annot
                    opt_dims
                    opt_initializer

opt_dims        ::= dims
                  | ε

dims            ::= '[' expr ']' { '[' expr ']' }

opt_initializer ::= '=' initializer
                  | ε

initializer     ::= expr
                  | value_list

value_list      ::= expr ',' expr { ',' expr }
                    (* ≥ 2 elementos *)

set_stmt        ::= 'set' lvalue ( '=' | '+=' ) expr

lvalue          ::= primary_lvalue
                    { '[' expr ']' | '.' ID }

primary_lvalue  ::= ID
                  | 'ohmy'

type_annot      ::= 'int'
                  | 'float'
                  | 'text'
                  | 'bool'
                  | ID

func_def        ::= 'func' ID '(' [ param_list ] ')' block
param_list      ::= param { ',' param }

param           ::= ID ':' type_annot opt_dims

mold_def        ::= 'mold' ID '{' { mold_member } '}'

mold_member     ::= let_stmt
                  | func_def

if_stmt         ::= 'if' expr block [ 'otherwise' block ]
while_stmt      ::= 'asLongAs' expr block

for_stmt        ::= 'for'
                    '(' for_init ',' expr ',' for_update ')'
                    block

for_init        ::= let_stmt_simple

for_update      ::= set_stmt_simple
                  | expr

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
                  | 'ohmy'
                  | 'ohmy' '.' ID
                  | '(' expr ')'
                  | ID
                  | INT_LIT
                  | FLOAT_LIT
                  | STRING
                  | 'indeed'
                  | 'nope'
                  | 'nothing'

arg_list        ::= expr { ',' expr }
──────────────────────────────────────────────────────────────────
"""

import ply.yacc as yacc
from .analizador_lexico import AnalizadorLexico
from .analizador_sintactico import AnalizadorSintactico
from .semantic_ast_annotator import ASTSemanticAnnotator
from .ast_nodos import (
    Nodo,
    NodoDeclaracion,
    NodoFuncion,
    NodoID,
    NodoMold,
    NodoParametro,
    NodoTerminal
)


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
    precedence = AnalizadorSintactico.precedence

    _SEMANTIC_META_KEYS = {
        'tipo',
        'tipo_semantico',
        'dims',
        'kind',
        'return_type',
        'params_info',
        'scope_id',
        'tipo_decl',
        'semantic_info',
        'text_size',
    }

    # GRAMÁTICA CON LÓGICA SEMÁNTICA (SIN CONSTRUCCIÓN DE NODOS)

    # PROGRAMA
    def p_program(self, p):
        """program : stmt_list"""
        # Simplemente ejecutar análisis semántico del programa
        pass

    def p_stmt_list_multi(self, p):
        """stmt_list : stmt_list statement"""

        previous_returns = p[1]['always_returns']

        if previous_returns:

            self._emit_error(
                p.lineno(2),
                "código inalcanzable"
            )

        current_returns = p[2].get(
            'always_returns',
            False
        )

        p[0] = {
            'always_returns': (
                previous_returns
                or
                current_returns
            )
        }

    def p_stmt_list_empty(self, p):
        """stmt_list : empty"""

        p[0] = {
            'always_returns': False
        }

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

        p[0] = p[1]

    # ── Declaración let
    def p_let_stmt(self, p):
        """
        let_stmt : LET ID COLON type_annot opt_dims opt_initializer
        """

        name = p[2]
        type_name = self._get_type_name_from_token(p[4])

        declared_dims = p[5]['dims']
        declared_shape = p[5]['shape']

        initializer = p[6]

        if not self._type_exists(type_name):

            self._emit_error(
                p.lineno(3),
                f"tipo '{type_name}' no existe"
            )

        value = None

        if initializer is not None:

            expr_type = self._extract_type(initializer)
            expr_dims = self._extract_dims(initializer)

            compatible = (
                type_name == expr_type
                or (
                    type_name == 'float'
                    and expr_type == 'int'
                )
            )

            if not compatible:

                self._emit_error(
                    p.lineno(1),
                    f"asignación incompatible: "
                    f"no se puede asignar "
                    f"'{expr_type}' a '{type_name}'"
                )

            if not self._is_flat_initializer(initializer):

                if declared_dims != expr_dims:

                    self._emit_error(
                        p.lineno(1),
                        f"dimensiones incompatibles: "
                        f"se esperaba {declared_dims}D "
                        f"y se recibió {expr_dims}D"
                    )

            if self._is_flat_initializer(initializer):

                expected_size = self._shape_size(
                    declared_shape
                )

                received_size = initializer.get(
                    'flat_size',
                    0
                )

                if expected_size != received_size:

                    self._emit_error(
                        p.lineno(1),
                        f"tamaño incompatible: "
                        f"se esperaban {expected_size} elementos "
                        f"y se recibieron {received_size}"
                    )

            init_size = self._flatten_size(initializer)

            declared_size = self._shape_size(
                declared_shape
            )

            if (
                declared_dims > 0
                and
                declared_size != init_size
            ):

                self._emit_error(
                    p.lineno(1),
                    f"tamaño incompatible: "
                    f"se esperaban {declared_size} elementos "
                    f"y se recibieron {init_size}"
                )

            value = self._extract_value(initializer)

        kind = (
            'array'
            if declared_dims > 0
            else 'variable'
        )

        self._define_symbol(
            name,
            kind,
            type_name,
            p.lineno(1),
            dims=declared_dims,
            shape=declared_shape,
            value=value
        )

        p[0] = {
            'always_returns': False
        }

    def p_opt_dims(self, p):
        """opt_dims : dims
                    | empty"""

        if p[1] is None:

            p[0] = {
                'dims': 0,
                'shape': []
            }

            return

        p[0] = p[1]

    def p_dims_one(self, p):
        """dims : LBRACKET expr RBRACKET"""

        expr_type = self._extract_type(p[2])

        if expr_type != 'int':

            self._emit_error(
                p.lineno(1),
                "las dimensiones deben ser int"
            )

        p[0] = {
            'dims': 1,
            'shape': [
                self._extract_value(p[2])
            ]
        }

    def p_dims_many(self, p):
        """dims : dims LBRACKET expr RBRACKET"""

        expr_type = self._extract_type(p[3])

        if expr_type != 'int':

            self._emit_error(
                p.lineno(2),
                "las dimensiones deben ser int"
            )

        shape = list(p[1]['shape'])

        shape.append(
            self._extract_value(p[3])
        )

        p[0] = {
            'dims': p[1]['dims'] + 1,
            'shape': shape
        }

    def p_opt_initializer_empty(self, p):
        """
        opt_initializer : empty
        """

        p[0] = None


    def p_opt_initializer_assign(self, p):
        """
        opt_initializer : ASSIGN initializer
        """

        p[0] = p[2]

    def p_initializer_expr(self, p):
        """initializer : expr"""
        p[0] = p[1]

    def p_initializer_list(self, p):
        """initializer : value_list"""

        p[0] = p[1]

    def p_value_list_start(self, p):
        """
        value_list : expr COMMA expr
        """

        left_type = self._extract_type(p[1])
        right_type = self._extract_type(p[3])

        if left_type != right_type:

            self._emit_error(
                p.lineno(2),
                "lista con tipos incompatibles"
            )

        left_dims = self._extract_dims(p[1])
        right_dims = self._extract_dims(p[3])

        if left_dims != right_dims:

            self._emit_error(
                p.lineno(2),
                "lista con dimensiones incompatibles"
            )

        values = []

        values.extend(
            self._flatten_values(p[1])
        )

        values.extend(
            self._flatten_values(p[3])
        )

        p[0] = {
            'type': left_type,
            'value': values,
            'dims': None,
            'item_dims': left_dims,
            'is_flat': True,
            'flat_size': len(values)
        }

    def p_value_list_grow(self, p):
        """
        value_list : value_list COMMA expr
        """

        current_type = p[1]['type']
        new_type = self._extract_type(p[3])

        if current_type != new_type:

            self._emit_error(
                p.lineno(2),
                "lista con tipos incompatibles"
            )

        current_dims = p[1].get('item_dims', 0)
        new_dims = self._extract_dims(p[3])

        if current_dims != new_dims:

            self._emit_error(
                p.lineno(2),
                "lista con dimensiones incompatibles"
            )

        values = list(p[1]['value'])

        values.extend(
            self._flatten_values(p[3])
        )

        p[0] = {
            'type': current_type,
            'value': values,
            'dims': None,
            'item_dims': current_dims,
            'is_flat': True,
            'flat_size': len(values)
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
                if sym.get('type') == 'text':
                    sym['text_size'] = max(
                        int(sym.get('text_size') or 0),
                        self._text_value_size(sym['value'])
                    )
        
        p[0] = {
            'always_returns': False
        }

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
                if sym.get('type') == 'text':
                    sym['text_size'] = int(sym.get('text_size') or 0)
        
        p[0] = {
            'always_returns': False
        }

    # ── Lvalue
    def p_lvalue_id(self, p):
        """lvalue : ID"""
        name = p[1]

        if self.current_method_mold is not None:
            mold = self._resolve_ohmy(p.lineno(1))
            if mold is not None and name in mold.get('fields', {}):
                self._emit_error(
                    p.lineno(1),
                    f"el miembro '{name}' del mold '{self.current_method_mold}' debe accederse con ohmy"
                )
                p[0] = '__invalid_field_access__'
                return

        p[0] = name

    def p_lvalue_ohmy(self, p):
        """lvalue : OHMY"""

        mold = self._resolve_ohmy(
            p.lineno(1)
        )

        if mold is None:

            p[0] = '__invalid_ohmy__'
            return

        p[0] = {
            'kind': 'ohmy',
            'type': self.current_method_mold
        }

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
        params = p[5]

        self._define_symbol(
            name,
            'function',
            'void',
            p.lineno(1),
            value=None
        )

        sym = self._resolve_symbol(name)

        if sym is not None:
            sym['params'] = params
            num_params = len(params)
            param_names = {p_info['name']: i for i, p_info in enumerate(params)}
            updated = 0
            for sym_entry in reversed(self.defined_symbols):
                if sym_entry.get('kind') == 'parameter' and sym_entry.get('name') in param_names and sym_entry.get('scope') == name:
                    idx = param_names[sym_entry['name']]
                    # CALL pushes arguments right-to-left and then pushes the
                    # return address; the callee prologue adds its frame size,
                    # so the first declared parameter sits at frame_size + 16
                    # plus one 8-byte slot for each later parameter.
                    sym_entry['param_offset'] = (sym.get('frame_size') or 0) + (num_params - idx + 1) * 8
                    updated += 1
                    if updated == num_params:
                        break

            inferred_return = 'void'

            if self.current_function is not None:
                inferred_return = (
                    self.current_function['return_type']
                    or 'void'
                )

            sym['return_type'] = inferred_return
            sym['return_info'] = (
                self.current_function.get('return_info')
                or {
                    'type': 'void',
                    'dims': 0,
                    'shape': []
                }
            )
            if self.current_method_mold is not None:

                mold = self.molds.get(
                    self.current_method_mold
                )

                if mold is not None:

                    method = mold['methods'].get(name)
                    if method is not None:

                        method['params'] = params
                        method['return_type'] = inferred_return
                        method['return_info'] = sym['return_info']

            body_returns = p[7]['always_returns']

            if (
                inferred_return != 'void'
                and
                not body_returns
            ):

                self._emit_error(
                    p.lineno(1),
                    f"la función '{name}' no retorna en todos los caminos"
                )
            frame_size = self.function_stack_offsets.pop()
            if frame_size % 8 != 0:
                frame_size += 8 - (frame_size % 8)
            sym['frame_size'] = frame_size
            self._enrich_lexer_symbol_entry(name, sym)
            self.current_function = None
            self.current_method_mold = None
        p[0] = {
            'always_returns': False
        }

    def p_enter_function_scope(self, p):
        """enter_function_scope :"""

        function_name = p[-2]

        self.current_function = {
            'name': function_name,
            'return_type': None,
            'return_info': {
                'type': 'void',
                'dims': 0,
                'shape': []
            },
            'mold': self.current_mold,
            'has_deliver': False
        }

        self.current_method_mold = self.current_mold

        # Keep function scope case-sensitive so func/Func/FUNC remain distinct.
        self._enter_scope(function_name)
        self.function_stack_offsets.append(0)

    def p_func_def_no_params(self, p):
        """func_def : FUNC ID LPAREN enter_function_scope RPAREN block"""

        name = p[2]

        self._define_symbol(
            name,
            'function',
            'void',
            p.lineno(1),
            value=None
        )

        sym = self._resolve_symbol(name)

        if sym is not None:
            sym['params'] = []
            inferred_return = 'void'

            if self.current_function is not None:
                inferred_return = (
                    self.current_function['return_type']
                    or 'void'
                )

            sym['return_type'] = inferred_return
            sym['return_info'] = (
                self.current_function.get('return_info')
                or {
                    'type': 'void',
                    'dims': 0,
                    'shape': []
                }
            )
            if self.current_method_mold is not None:

                mold = self.molds.get(
                    self.current_method_mold
                )

                if mold is not None:

                    method = mold['methods'].get(name)

                    if method is not None:

                        method['params'] = []
                        method['return_type'] = inferred_return
                        method['return_info'] = sym['return_info']
            
            body_returns = p[6]['always_returns']

            if (
                inferred_return != 'void'
                and
                not body_returns
            ):

                self._emit_error(
                    p.lineno(1),
                    f"la función '{name}' no retorna en todos los caminos"
                )
            frame_size = self.function_stack_offsets.pop()
            if frame_size % 8 != 0:
                frame_size += 8 - (frame_size % 8)
            sym['frame_size'] = frame_size
            self._enrich_lexer_symbol_entry(name, sym)
            self.current_function = None
            self.current_method_mold = None
        
        p[0] = {
            'always_returns': False
        }

    def p_param_list_one(self, p):
        """param_list : param"""

        p[0] = [p[1]]

    def p_param_list_many(self, p):
        """param_list : param_list COMMA param"""

        p[0] = p[1] + [p[3]]

    def p_param(self, p):
        """
        param : ID COLON type_annot opt_dims
        """

        name = p[1]
        type_name = p[3]

        dims_info = p[4]

        self._define_symbol(
            name,
            'parameter',
            type_name,
            p.lineno(1),
            dims=dims_info['dims'],
            shape=dims_info['shape']
        )

        p[0] = {
            'name': name,
            'type': type_name,
            'dims': dims_info['dims'],
            'shape': dims_info['shape']
        }

    # ── Mold
    def p_mold_def(self, p):
        """mold_def : MOLD ID LBRACE enter_mold_scope mold_body RBRACE"""

        name = p[2]

        mold_info = self.molds.get(name, {})

        attrs = list(
            mold_info.get('fields', {}).keys()
        )

        fields = mold_info.get('fields', {})

        # IMPORTANTE
        self._leave_scope()

        self.current_mold = None

        self._define_symbol(
            name,
            'mold',
            name,
            p.lineno(1)
        )

        sym = self._resolve_symbol(name)

        if sym is not None:

            sym['attr'] = attrs
            sym['fields'] = fields
            sym['size'] = mold_info.get('size',0)
            sym['field_order'] = mold_info.get(
                'field_order',
                []
            )
            sym['methods'] = mold_info.get('methods', {})
            self._enrich_lexer_symbol_entry(
                name,
                sym
            )

        p[0] = {
            'always_returns': False
        }

    def p_enter_mold_scope(self, p):
        """enter_mold_scope :"""
        
        mold_name = p[-2]

        self.current_mold = mold_name

        self.molds[mold_name] = {
            'fields': {},
            'methods': {},
            'attrs': []
        }

        self._enter_scope('mold')

    def p_mold_body_multi(self, p):
        """mold_body : mold_body mold_member"""
        p[0] = {
            'always_returns': False
        }

    def p_mold_body_empty(self, p):
        """mold_body : empty"""
        p[0] = {
            'always_returns': False
        }

    def p_mold_member(self, p):
        """mold_member : let_stmt
                       | func_def"""
        p[0] = p[1]

    # ── if / otherwise
    def p_if_simple(self, p):
        """if_stmt : IF expr enter_if_scope block"""

        cond_type = self._extract_type(p[2])

        if cond_type != 'bool':

            self._emit_error(
                p.lineno(1),
                "la condición del if debe ser bool"
            )

        p[0] = {
            'always_returns': False
        }

    def p_enter_if_scope(self, p):
        """enter_if_scope :"""
        self._enter_scope('if')

    def p_if_otherwise(self, p):
        """if_stmt : IF expr enter_if_scope block OTHERWISE enter_else_scope block"""

        cond_type = self._extract_type(p[2])

        if cond_type != 'bool':

            self._emit_error(
                p.lineno(1),
                "la condición del if debe ser bool"
            )

        then_returns = p[4]['always_returns']
        else_returns = p[7]['always_returns']

        p[0] = {
            'always_returns': (
                then_returns
                and
                else_returns
            )
        }

    def p_enter_else_scope(self, p):
        """enter_else_scope :"""
        self._enter_scope('else')

    # ── asLongAs (while)
    def p_while(self, p):
        """while_stmt : ASLONGAS expr enter_while_scope block"""
        cond_type = self._extract_type(p[2])

        if cond_type != 'bool':

            self._emit_error(
                p.lineno(1),
                "la condición del while debe ser bool"
            )

        p[0] = {
            'always_returns': False
        }
    
    def p_enter_while_scope(self, p):
        """enter_while_scope :"""
        self._enter_scope('while')

    # ── for
    def p_for(self, p):
        """for_stmt : FOR LPAREN enter_for_scope for_init COMMA expr COMMA for_update RPAREN block"""
        cond_type = self._extract_type(p[6])

        if cond_type != 'bool':

            self._emit_error(
                p.lineno(1),
                "la condición del for debe ser bool"
            )

        p[0] = {
            'always_returns': False
        }

    def p_enter_for_scope(self, p):
        """enter_for_scope :"""
        self._enter_scope('for')

    def p_for_init_let(self, p):
        """for_init : LET ID COLON type_annot ASSIGN expr"""
        name = p[2]
        type_name = self._get_type_name_from_token(p[4])

        expr_data = p[6]

        expr_type = self._extract_type(expr_data)

        compatible = (
            type_name == expr_type
            or
            (
                type_name == 'float'
                and expr_type == 'int'
            )
        )

        if not compatible:

            self._emit_error(
                p.lineno(5),
                f"asignación incompatible: "
                f"no se puede asignar "
                f"'{expr_type}' a '{type_name}'"
            )

        if not self._type_exists(type_name):
            self._emit_error(
                p.lineno(3),
                f"tipo '{type_name}' no existe"
            )
        self._define_symbol(
            name,
            'variable',
            type_name,
            p.lineno(1),
            value=self._extract_value(p[6])
        )
        p[0] = {
            'always_returns': False
        }

    def p_for_update_set_assign(self, p):
        """for_update : SET lvalue ASSIGN expr"""
        p[0] = {
            'always_returns': False
        }

    def p_for_update_set_pluseq(self, p):
        """for_update : SET lvalue SWEET_PLUS expr"""
        p[0] = {
            'always_returns': False
        }

    def p_for_update_expr(self, p):
        """for_update : expr"""
        p[0] = {
            'always_returns': False
        }

    # ── Sentencias simples
    def p_deliver_val(self, p):
        """deliver_stmt : DELIVER expr"""

        if self.current_function is None:

            self._emit_error(
                p.lineno(1),
                "deliver solo puede usarse dentro de una función"
            )

            return

        expr_type = self._extract_type(p[2])

        current_return = self.current_function['return_type']

        # Primer deliver → inferir tipo
        if current_return is None:
            self.current_function['return_info'] = {
                'type': expr_type,
                'dims': self._extract_dims(p[2]),
                'shape': self._extract_shape(p[2]),
            }
            self.current_function['return_type'] = expr_type
            self.current_function['has_deliver'] = True

            p[0] = {
                'always_returns': True
            }

            return

        current_info = self.current_function.get(
            'return_info',
            {}
        )

        current_dims = current_info.get('dims', 0)
        expr_dims = self._extract_dims(p[2])

        current_shape = current_info.get('shape', [])
        expr_shape = self._extract_shape(p[2])

        dims_compatible = (
            current_dims == expr_dims
        )
        compatible = (
            (
                current_return == expr_type
                or
                (
                    current_return == 'float'
                    and expr_type == 'int'
                )
            )
            and
            dims_compatible and current_shape == expr_shape
        )

        if not compatible:

            self._emit_error(
                p.lineno(1),
                f"la función '{self.current_function['name']}' "
                f"retorna tipos incompatibles "
                f"('{current_return}' y '{expr_type}')"
            )

        p[0] = {
            'always_returns': True
        }
        self.current_function['has_deliver'] = True

    def p_deliver_nothing(self, p):
        """deliver_stmt : DELIVER"""

        if self.current_function is None:

            self._emit_error(
                p.lineno(1),
                "deliver solo puede usarse dentro de una función"
            )

            return

        current_return = self.current_function['return_type']

        if current_return is None:

            self.current_function['return_type'] = 'void'
            self.current_function['has_deliver'] = True
            self.current_function['return_info'] = {
                'type': 'void',
                'dims': 0,
                'shape': []
            }

            p[0] = {
                'always_returns': True
            }

            return

        if current_return != 'void':

            self._emit_error(
                p.lineno(1),
                f"la función '{self.current_function['name']}' "
                f"retorna tipos incompatibles "
                f"('{current_return}' y 'void')"
            )
        
        p[0] = {
            'always_returns': True
        }
        self.current_function['has_deliver'] = True

    def p_show(self, p):
        """show_stmt : SHOW expr"""

        p[0] = {
            'always_returns': False
        }

    def p_oops(self, p):
        """oops_stmt : OOPS expr"""

        p[0] = {
            'always_returns': False
        }

    def p_expr_stmt(self, p):
        """expr_stmt : expr"""

        p[0] = {
            'always_returns': False
        }

    # ── Bloque
    def p_block(self, p):
        """block : LBRACE stmt_list RBRACE"""

        self._leave_scope()

        p[0] = p[2]

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
        expr_type = self._extract_type(p[2])

        if expr_type not in ('int', 'float'):
            self._emit_error(
                p.lineno(1),
                "el operador unario '-' requiere un valor numérico"
            )

        p[0] = self._make_expr_data(
            expr_type,
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

        target_dims = self._extract_dims(target)

        if target_dims <= 0:

            self._emit_error(
                p.lineno(2),
                "el símbolo no es indexable"
            )

            p[0] = self._make_expr_data('unknown')
            return

        target_shape = self._extract_shape(target)

        remaining_shape = (
            target_shape[1:]
            if len(target_shape) > 0
            else []
        )

        p[0] = self._make_expr_data(
            self._extract_type(target),
            None,
            dims=max(target_dims - 1, 0),
            shape=remaining_shape
        )

    def p_expr_method_call(self, p):
        """expr : expr DOT ID LPAREN arg_list RPAREN
                | expr DOT ID LPAREN RPAREN"""

        target = p[1]
        method_name = p[3]

        if len(p) == 7:
            received_args = p[5]
        else:
            received_args = []

        target_type = self._extract_type(target)

        if self._validate_extern_function(method_name, self.metadata):

            self._emit_error(
                p.lineno(3),
                f"la función externa '{method_name}' no puede llamarse como método"
            )

            p[0] = self._make_expr_data(
                'unknown',
                None
            )

            return

        mold = self.molds.get(target_type)

        if mold is None:

            self._emit_error(
                p.lineno(2),
                f"'{target_type}' no es un mold"
            )

            p[0] = self._make_expr_data(
                'unknown',
                None
            )

            return

        method = mold['methods'].get(method_name)

        if method is None:

            self._emit_error(
                p.lineno(2),
                f"el mold '{target_type}' "
                f"no tiene método '{method_name}'"
            )

            p[0] = self._make_expr_data(
                'unknown',
                None
            )

            return

        expected_params = method.get(
            'params',
            []
        )

        self._validate_call_arguments(
            p.lineno(2),
            expected_params,
            received_args
        )

        return_info = method.get('return_info', {})

        p[0] = self._make_expr_data(
            return_info.get('type', 'void'),
            None,
            return_info.get('dims', 0),
            return_info.get('shape', [])
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
            field.get('dims', 0),
            field.get('shape', []),
            field.get('text_size', 0)
        )

    def p_expr_call_args(self, p):
        """expr : ID LPAREN arg_list RPAREN"""
        # Validar que función existe
        name = p[1]
        sym = self._resolve_symbol(name)

        if sym is None:

            isExtern = self._validate_extern_function(name, self.metadata)

            if not isExtern:
                self._emit_error(
                    p.lineno(1),
                    f"función '{name}' no declarada"
                )

                p[0] = self._make_expr_data('unknown')
                return
            p[0] = self._make_expr_data(
                'void',
                None
            )
            return

        if sym.get('kind') != 'function':

            self._emit_error(
                p.lineno(1),
                f"'{name}' no es una función"
            )

            p[0] = self._make_expr_data('unknown')
            return
        
        expected_params = sym.get('params', [])

        self._validate_call_arguments(
            p.lineno(1),
            expected_params,
            p[3]
        )
        
        ret = sym.get('return_info', {})

        p[0] = self._make_expr_data(
            ret.get('type', 'void'),
            None,
            ret.get('dims', 0),
            ret.get('shape', [])
        )

    def p_expr_call_noargs(self, p):
        """expr : ID LPAREN RPAREN"""
        name = p[1]
        sym = self._resolve_symbol(name)

        if sym is None:

            if not self._validate_extern_function(name, self.metadata):

                self._emit_error(
                    p.lineno(1),
                    f"función '{name}' no declarada"
                )

                p[0] = self._make_expr_data('unknown')
                return

            p[0] = self._make_expr_data(
                'void',
                None
            )
            return

        if sym.get('kind') != 'function':

            self._emit_error(
                p.lineno(1),
                f"'{name}' no es una función"
            )

            p[0] = self._make_expr_data('unknown')
            return
        
        expected_params = sym.get('params', [])

        if len(expected_params) != 0:

            self._emit_error(
                p.lineno(1),
                f"la función '{name}' requiere argumentos"
            )
        
        ret = sym.get('return_info', {})

        p[0] = self._make_expr_data(
            ret.get('type', 'void'),
            None,
            ret.get('dims', 0),
            ret.get('shape', [])
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
                'unknown',
                None
            )

            return

        self._validate_summon_arguments(
            p.lineno(1),
            mold_name,
            p[4]
        )

        p[0] = self._make_expr_data(
            mold_name,
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
                'unknown',
                None
            )

            return

        mold = self.molds.get(mold_name)

        expected_fields = mold.get('field_order', [])

        if len(expected_fields) != 0:

            self._emit_error(
                p.lineno(1),
                f"el mold '{mold_name}' requiere argumentos"
            )

        p[0] = self._make_expr_data(
            mold_name,
            None
        )

    def p_expr_ohmy_member(self, p):
        """expr : OHMY DOT ID"""

        mold = self._resolve_ohmy(
            p.lineno(1)
        )

        if mold is None:

            p[0] = self._make_expr_data(
                'unknown',
                None
            )

            return

        member = p[3]

        field = mold['fields'].get(member)

        if field is None:

            self._emit_error(
                p.lineno(3),
                f"el mold '{self.current_method_mold}' "
                f"no tiene miembro '{member}'"
            )

            p[0] = self._make_expr_data(
                'unknown',
                None
            )

            return

        p[0] = self._make_expr_data(
            field['type'],
            None,
            field.get('dims', 0),
            field.get('shape', []),
            field.get('text_size', 0)
        )

    def p_expr_ohmy(self, p):
        """expr : OHMY"""

        mold = self._resolve_ohmy(
            p.lineno(1)
        )

        if mold is None:

            p[0] = self._make_expr_data(
                'unknown',
                None
            )

            return

        p[0] = self._make_expr_data(
            self.current_method_mold,
            None
        )

    def p_expr_group(self, p):
        """expr : LPAREN expr RPAREN"""
        p[0] = p[2]

    def p_expr_id(self, p):
        """expr : ID"""

        name = p[1]

        if self.current_method_mold is not None:
            mold = self._resolve_ohmy(p.lineno(1))
            if mold is not None and name in mold.get('fields', {}):
                self._emit_error(
                    p.lineno(1),
                    f"el miembro '{name}' del mold '{self.current_method_mold}' debe accederse con ohmy"
                )
                p[0] = self._make_expr_data('unknown')
                return

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
            sym.get('dims', 0),
            shape=sym.get('shape', [])
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
        pool_entry = self._intern_string(p[1])
        p[0] = self._make_expr_data(
            'text',
            pool_entry
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

        p[0] = [p[1]]

    def p_arg_list_many(self, p):
        """arg_list : arg_list COMMA expr"""

        p[0] = p[1] + [p[3]]

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

    # INICIALIZACIÓN Y API PÚBLICA

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
        self.current_method_mold = None
        self.parser = yacc.yacc(
            module=self,
            debug=False,
            write_tables=False,
        )
        self.current_function = None
        self.pending_params = []
        self._ast_annotator = ASTSemanticAnnotator(self)
        self.metadata = []
        self.type_sizes = {
            'int':8,
            'float':8,
            'bool':8,
            'text':8,
        }
        self.function_stack_offsets = []
        self.string_pool = {}
        self.string_counter = 0
        self.float_pool = {}
        self.float_counter = 0

    def parse(self, codigo: str, metadata:list) -> tuple[list[str], object, dict]:
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
        self.metadata = metadata

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
                'scope_id': row.get('scope_id'),
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

        # Paso 2: Obtener el AST sintáctico
        _, ast = self._syntactic.parse(codigo)
        self._annotate_ast(ast)
        return {
            'errors': self.errors,
            'ast': ast,
            'symbol_table': self.semantic_symbol_table,
            'molds': self.molds,
            'type_sizes': self.type_sizes,
            'defined_symbols': self.defined_symbols,
            'functions': self._collect_function_entries(),
            'target': {
                'pointer_size': 8,
                'word_size': 8,
                'stack_alignment': 8,
            },
            'string_pool': self.string_pool,
            'float_pool': self.float_pool,
        }
    
    def _sizeof(self, type_name, dims=0, shape=None):

        if type_name in self.type_sizes:
            base_size = self.type_sizes[type_name]
        else:
            mold = self.molds.get(type_name)

            if mold:
                base_size = mold.get('size', 0)
            else:
                base_size = 0

        if dims <= 0:
            return base_size

        total_items = self._shape_size(shape)

        if total_items is None:
            return base_size

        return base_size * total_items

    def _make_expr_data(
        self,
        type_name,
        value=None,
        dims=0,
        shape=None,
        text_size=0
    ):
        return {
            'type': type_name,
            'value': value,
            'dims': dims,
            'shape': shape or [],
            'text_size': text_size,
        }
    
    def _collect_function_entries(self):
        result = {}
        for sym in self.defined_symbols:
            if sym.get('kind') in ('function', 'method'):
                result[sym['name']] = {
                    'label': sym.get('label'),
                    'return_info': sym.get('return_info'),
                    'params': sym.get('params', []),
                    'frame_size': sym.get('frame_size', 0),
                }
        return result

    def _compact_params_info(self, params):
        if not isinstance(params, list):
            return None
        compact = []
        for param in params:
            if not isinstance(param, dict):
                continue
            data = {}
            if param.get('name') is not None:
                data['name'] = param.get('name')
            if param.get('type') is not None:
                data['type'] = param.get('type')
            if param.get('dims', 0):
                data['dims'] = param.get('dims', 0)
            if data:
                compact.append(data)
        return compact

    def _make_semantic_info(self, type_name='unknown', dims=0, symbol=None, scope_id=None, value=None):
        """Construir el paquete semántico normalizado para un subárbol."""
        info = {
            'type': type_name,
            'dims': dims,
        }
        if isinstance(symbol, dict):
            kind = symbol.get('kind')
            if kind is not None:
                info['kind'] = kind
            if scope_id is None:
                scope_id = symbol.get('scope_id')
            if symbol.get('return_type') is not None:
                info['return_type'] = symbol.get('return_type')
            if symbol.get('text_size') is not None:
                info['text_size'] = symbol.get('text_size')
            compact_params = self._compact_params_info(symbol.get('params'))
            if compact_params is not None:
                info['params_info'] = compact_params
        if scope_id is not None:
            info['scope_id'] = scope_id
        if value is not None:
            info['value'] = value
        return info

    def _is_numeric_type(self, type_name) -> bool:
        return type_name in {'int', 'float'}

    def _promote_numeric_types(self, left_type, right_type):
        if left_type == 'float' or right_type == 'float':
            return 'float'
        if left_type == 'int' and right_type == 'int':
            return 'int'
        return 'unknown'

    def _make_scope_id(self, scope_name: str | None, line: int | None = None):
        if scope_name is None:
            scope_name = 'unknown'
        if line is None:
            return scope_name
        return f'{scope_name}@{line}'

    def _set_node_semantics(self, node, *, type_name='unknown', dims=0, symbol=None, scope_id=None, value=None):
        """Anotar un nodo sin alterar los campos estructurales existentes."""
        if node is None or not isinstance(node, Nodo):
            return self._make_semantic_info(type_name, dims, symbol=symbol, scope_id=scope_id, value=value)

        if not isinstance(node, NodoTerminal):
            node.set_type(type_name, dims)
            if symbol is not None:
                node.merge_symbol_metadata(symbol)
            if hasattr(node, 'symbol'):
                delattr(node, 'symbol')
            if scope_id is not None:
                node.scope_id = scope_id
            elif symbol is not None and isinstance(symbol, dict):
                node.scope_id = symbol.get('scope_id')

        effective_symbol = symbol if getattr(node, '_allows_symbol', False) else None
        info = self._make_semantic_info(type_name, dims, symbol=effective_symbol, scope_id=scope_id, value=value)
        node.semantic_info = info
        return info

    def _node_line(self, node) -> int:
        if node is None:
            return 0
        return getattr(node, 'linea', 0) or 0

    def _node_symbol_info(self, symbol: dict | None):
        if symbol is None:
            return None
        return self._make_semantic_info(
            symbol.get('type', 'unknown'),
            symbol.get('dims', 0),
            symbol=symbol,
            scope_id=symbol.get('scope_id'),
            value=symbol.get('value')
        )

    def _semantic_children(self, node):
        """Iterar solo por hijos del AST, ignorando metadatos semánticos."""
        if not isinstance(node, Nodo):
            return
        for name, child in list(node.__dict__.items()):
            if name.startswith('_'):
                continue
            if name in self._SEMANTIC_META_KEYS:
                continue
            if child is None:
                continue
            if isinstance(child, (Nodo, list, tuple)):
                yield name, child

    def _resolve_field_from_mold(self, mold_name: str, member_name: str):
        mold = self.molds.get(mold_name)
        if mold is None:
            return None
        return mold.get('fields', {}).get(member_name)

    def _resolve_method_from_mold(self, mold_name: str, method_name: str):
        mold = self.molds.get(mold_name)
        if mold is None:
            return None
        return mold.get('methods', {}).get(method_name)

    def _node_name(self, node):
        if node is None:
            return None
        if isinstance(node, str):
            return node
        if isinstance(node, NodoTerminal):
            return node.valor
        if isinstance(node, NodoID):
            return node.nombre
        if isinstance(node, NodoDeclaracion):
            return self._node_name(node.nombre)
        if isinstance(node, NodoParametro):
            return self._node_name(node.nombre)
        if isinstance(node, (NodoFuncion, NodoMold)):
            return self._node_name(node.nombre)
        return getattr(node, 'nombre', None)

    def _extract_type(self, expr_data):
        if isinstance(expr_data, dict):
            return expr_data.get('type')
        if isinstance(expr_data, Nodo):
            return getattr(expr_data, 'tipo', None)
        return expr_data

    def _extract_value(self, expr_data):
        if isinstance(expr_data, dict):
            return expr_data.get('value')
        if isinstance(expr_data, Nodo):
            return getattr(expr_data, 'valor', None)
        return None
    
    def _extract_dims(self, expr_data):
        if isinstance(expr_data, dict):
            return expr_data.get('dims', 0)
        if isinstance(expr_data, Nodo):
            return getattr(expr_data, 'dims', 0) or 0
        return 0
    
    def _type_exists(self, type_name):

        primitive_types = {
            'int',
            'float',
            'text',
            'bool',
            'void'
        }

        if type_name in primitive_types:
            return True

        return type_name in self.molds
    
    def _validate_call_arguments(
        self,
        line,
        expected_params,
        received_args
    ):

        if len(expected_params) != len(received_args):

            self._emit_error(
                line,
                f"se esperaban {len(expected_params)} argumentos "
                f"y se recibieron {len(received_args)}"
            )

            return False

        for expected, received in zip(expected_params, received_args):

            expected_type = expected['type']
            expected_dims = expected.get('dims', 0)

            received_type = self._extract_type(received)
            received_dims = self._extract_dims(received)

            # ── Validar dimensiones
            if expected_dims != received_dims:

                self._emit_error(
                    line,
                    f"dimensiones incompatibles: "
                    f"se esperaba {expected_dims}D "
                    f"y se recibió {received_dims}D"
                )

                return False

            # ── Validar tipos
            compatible = (
                expected_type == received_type or
                (
                    expected_type == 'float' and
                    received_type == 'int'
                )
            )

            if not compatible:

                self._emit_error(
                    line,
                    f"argumento incompatible: "
                    f"se esperaba '{expected_type}' "
                    f"y se recibió '{received_type}'"
                )

                return False

        return True
    
    def _validate_summon_arguments(
        self,
        line,
        mold_name,
        received_args
    ):

        mold = self.molds.get(mold_name)

        if mold is None:
            return False

        expected_fields = mold.get('field_order', [])

        if len(expected_fields) != len(received_args):

            self._emit_error(
                line,
                f"el mold '{mold_name}' espera "
                f"{len(expected_fields)} argumentos "
                f"y recibió {len(received_args)}"
            )

            return False

        for expected, received in zip(expected_fields, received_args):

            expected_type = expected['type']
            expected_dims = expected.get('dims', 0)

            received_type = self._extract_type(received)
            received_dims = self._extract_dims(received)

            # ── Validar dimensiones
            if expected_dims != received_dims:

                self._emit_error(
                    line,
                    f"dimensiones incompatibles para "
                    f"'{expected['name']}': "
                    f"se esperaba {expected_dims}D "
                    f"y se recibió {received_dims}D"
                )

                return False

            compatible = (
                expected_type == received_type or
                (
                    expected_type == 'float' and
                    received_type == 'int'
                )
            )

            if not compatible:

                self._emit_error(
                    line,
                    f"argumento incompatible para "
                    f"'{expected['name']}': "
                    f"se esperaba '{expected_type}' "
                    f"y se recibió '{received_type}'"
                )

                return False

        return True
    
    def _flatten_size(self, expr_data):

        value = self._extract_value(expr_data)

        if isinstance(value, list):
            return len(value)

        return 1
    
    def _shape_size(self, shape):

        if not shape:
            return 1

        total = 1

        for dim in shape:

            if dim is None:
                return None

            total *= dim

        return total
    
    def _flatten_values(self, expr_data):

        value = self._extract_value(expr_data)

        if isinstance(value, list):
            return value

        return [value]
    
    def _is_flat_initializer(self, expr_data):

        if not isinstance(expr_data, dict):
            return False

        return expr_data.get('is_flat', False)

    def _resolve_lvalue_type(self, lvalue, line):

        if isinstance(lvalue, str):

            sym = self._resolve_symbol(lvalue)

            if sym is None:
                return None

            return {
                'type': sym.get('type'),
                'dims': sym.get('dims', 0),
                'symbol': sym,
                'scope_id': sym.get('scope_id')
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

                return {
                    'type': field.get('type'),
                    'dims': field.get('dims', 0),
                    'symbol': field,
                    'scope_id': target_info.get('scope_id')
                }

            elif kind == 'array_access':

                target_info = self._resolve_lvalue_type(
                    lvalue['target'],
                    line
                )

                if target_info is None:
                    return None

                dims = target_info.get('dims', 0)
                shape = list(target_info.get('shape', []))
                remaining_shape = shape[1:] if shape else []

                return {
                    'type': target_info['type'],
                    'dims': max(dims - 1, 0),
                    'symbol': target_info.get('symbol'),
                    'scope_id': target_info.get('scope_id'),
                    'shape': remaining_shape,
                }

        return None
    
    def _resolve_ohmy(self, line):

        if self.current_method_mold is None:

            self._emit_error(
                line,
                "ohmy solo puede usarse dentro de métodos de mold"
            )

            return None

        mold = self.molds.get(self.current_method_mold)

        if mold is None:

            self._emit_error(
                line,
                "mold actual inválido"
            )

            return None

        return mold

    def _reset_semantic_state(self):
        """Reinicializar estado semántico."""
        self.scopes = [{}]
        self.scope_names = ['global']
        self.defined_symbols = []
        self.semantic_symbol_table = {}
        self.current_function = None
        self.pending_params = []
        self.molds = {}
        self.current_mold = None
        self.current_method_mold = None
        self.string_pool = {}
        self.string_counter = 0

    def _intern_string(self, value: str):
        if value in self.string_pool:
            return self.string_pool[value]
        label = f'str_{self.string_counter}'
        self.string_counter += 1
        entry = {
            'label': label,
            'value': value,
            'size': len(value) + 1
        }
        self.string_pool[value] = entry
        return entry

    def _text_value_size(self, value):
        if isinstance(value, dict):
            size = value.get('size')
            if size is not None:
                return int(size or 0)
            inner_value = value.get('value')
            if isinstance(inner_value, str):
                return len(inner_value) + 1
        if isinstance(value, str):
            return len(value) + 1
        return 0

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
        name,
        kind,
        type_name,
        line,
        dims=0,
        value=None,
        shape=None
    ):
        """Definir un símbolo en el alcance actual."""
        current_scope = self.scopes[-1]
        if name in current_scope:
            scope_name = self.scope_names[-1] if self.scope_names else 'unknown'
            self._emit_error(line, f"símbolo '{name}' ya fue definido en '{scope_name}'")
            return False
        symbol_kind = kind
        base_size = self._sizeof(type_name, 0)
        total_size = self._sizeof(type_name, dims, shape)
        text_size = self._text_value_size(value) if type_name == 'text' else 0

        entry = {
            'name': name,
            'kind': symbol_kind,
            'line': line,
            'dims': dims,
            'shape': shape or [],
            'scope': self.scope_names[-1] if self.scope_names else 'unknown',
            'scope_id': self._make_scope_id(self.scope_names[-1] if self.scope_names else 'unknown', line),
            'storage_class': None,
            'offset': None,
            'size': total_size,
            'element_size': base_size,
            'alignment': base_size or 8,
            'text_size': text_size,
        }
        if symbol_kind in ('variable','array','parameter','field'):
            entry['type']=type_name
            entry['value']=value
            if symbol_kind == 'parameter':
                entry['storage_class'] = 'param'
                entry['parameter_index'] = len([
                    s for s in current_scope.values()
                    if s.get('kind') == 'parameter'
                ])
                entry['param_offset'] = (
                    24 +
                    entry['parameter_index'] * 8
                )
            else:
                entry['storage_class'] = 'local'
                inside_function = (
                    self.current_function is not None
                )
                if inside_function:
                    size = entry['size']
                    if type_name == 'text':
                        size += text_size
                        entry['size'] = size
                    entry['offset'] = self.function_stack_offsets[-1]
                    self.function_stack_offsets[-1] += size
        elif symbol_kind in ('function','method'):
            entry['return_info'] = {
                'type': 'void',
                'dims': 0,
                'shape': []
            }
            entry['params']=[]
            if self.current_mold is not None:
                entry['label'] = (
                    f'FUNC_{self.current_mold}_{name}'
                )
            else:
                entry['label'] = f'FUNC_{name}'
            entry['frame_size']=None
            entry['local_count']=0
        elif symbol_kind=='mold':
            entry['type']=type_name
            entry['size']=0
            entry['field_order']=[]
            entry['methods'] = {}
        current_scope[name] = entry
        self.defined_symbols.append(entry)
        self._enrich_lexer_symbol_entry(name, entry)
        if self.current_mold is not None:
            mold_data = self.molds[self.current_mold]
            if kind in ('variable', 'array') and self.current_function is None:
                entry['kind'] = 'field'
                mold_data['fields'][name] = entry
                mold_data.setdefault('field_order', []).append(entry)
                attrs = mold_data.setdefault('attrs', [])
                if name not in attrs:
                    attrs.append(name)
                field_offset = mold_data.get('size',0)
                entry['offset'] = field_offset
                entry['storage_class']='field'
                field_size = self._sizeof(
                    type_name,
                    dims,
                    shape
                )
                mold_data['size'] = (
                    field_offset
                    +
                    field_size
                )
            elif kind == 'function':
                entry['kind'] = 'method'
                entry.setdefault('params', [])
                entry.setdefault('return_type', None)
                mold_data['methods'][name] = entry
        return True

    def _enrich_lexer_symbol_entry(self, name: str, sem_entry: dict):
        """Enriquecer la entrada base del lexer con metadatos semánticos de yacc."""
        row = self.semantic_symbol_table.get(name)
        row['kind'] = sem_entry.get('kind')
        row['type'] = sem_entry.get('type')
        row['dims'] = sem_entry.get('dims', 0)
        row['shape'] = sem_entry.get('shape', [])
        row['size'] = sem_entry.get('size')
        row['value'] = sem_entry.get('value')
        row['scope'] = sem_entry.get('scope')
        row['scope_id'] = sem_entry.get('scope_id')
        row['attr'] = sem_entry.get('attr')
        row['fields'] = sem_entry.get('fields')
        row['frame_size'] = sem_entry.get('frame_size')
        row['params'] = sem_entry.get('params')
        row['return_type'] = sem_entry.get('return_type')
        row['return_info'] = sem_entry.get('return_info')
        row['text_size'] = sem_entry.get('text_size')
        ###
        line = sem_entry.get('line')
        if line is not None and line not in row.get('lines', []):
            row.setdefault('lines', []).append(line)

    def _resolve_symbol(self, name: str) -> dict | None:
        """Resolver un símbolo buscando en alcances de adentro hacia afuera."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def _extract_shape(self, data):
        if isinstance(data, dict):
            return data.get('shape', [])
        return []

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
        is_flat = (
            isinstance(expr_data, dict)
            and
            expr_data.get('is_flat', False)
        )

        if not is_flat:

            if declared_dims != expr_dims:

                self._emit_error(
                    line,
                    f"dimensiones incompatibles: "
                    f"se esperaba {declared_dims}D "
                    f"y se recibió {expr_dims}D"
                )

                return False

        if is_flat:

            target_shape = (
                target_info.get('symbol', {})
                .get('shape', [])
            )

            expected_size = self._shape_size(
                target_shape
            )

            received_size = expr_data.get(
                'flat_size',
                0
            )

            if expected_size != received_size:

                self._emit_error(
                    line,
                    f"tamaño incompatible: "
                    f"se esperaban {expected_size} elementos "
                    f"y se recibieron {received_size}"
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

    def _annotate_ast(self, node, _visited=None):
        return self._ast_annotator.annotate(node, _visited)

    def _validate_extern_function(self, name, import_metadata):
        for inst in import_metadata:
            if name in inst:
                return True
        return False
