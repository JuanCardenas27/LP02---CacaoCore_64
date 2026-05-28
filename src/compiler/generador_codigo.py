import ply.yacc as yacc
from .analizador_lexico import AnalizadorLexico
from .analizador_semantico import AnalizadorSemantico
from .gestor_de_registros import GestorRegistros


class GeneradorCodigo:
    """
    Parser LALR(1) para Choco.

    Uso:
        parser = AnalizadorSemantico()
        errores, ast = parser.parse(codigo_fuente)
    """

    # ── Tokens (lista completa del lenguaje) ───────────────────────────────
    tokens = AnalizadorLexico.tokens

    # ── Precedencia (de menor a mayor) ────────────────────────────────────
    precedence = AnalizadorSemantico.precedence
    

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
        final_code.extend(self.funcs)
        self.text = final_code

        p[0] = ['.data'] + self.data + ['.text'] + final_code



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
            defecto = "' '"
        elif p[4] == "bool":
            defecto = 0

        if self.sim_table[p[2]]['scope'] == 'global':
            
            decl = f'{p[2]} : {defecto}'

            self.data.append(decl)

            p[0] = {
                "code": [],
                "result": p[2],
                "sect": '.data'
            }
        else:
            decl = f'{p[2]} : {defecto}'

            self.data.append(decl)
            instr = f'MOVD [{p[2]}], {defecto}'
            p[0] = {
                "code": [instr],
                "result": p[2],
                "sect": '.data'
            }


    def _default_for_type(self, tipo):
        if tipo == 'float': return 0.0
        if tipo == 'text': return "' '"
        return 0

    def _handle_by_type(self, name, tipo, arg):

        n_code = []
        init_value = arg['result']
        if tipo == 'text':
            self.sim_table[name] = {}
            self.sim_table[name]['len'] = len(init_value)
            self.sim_table[name]['type'] = tipo

            for i, ch in enumerate(init_value):
                if i == 0:
                    self.data.append(f"{name} : '{ch}'")
                else:
                    self.data.append(f"{name}{i} : '{ch}'")
        
        elif 'temp' in arg:
            decl = f'{name} : 0'
            self.data.append(decl)
            n_code.extend([f'MOVD [{name}], {init_value}'])
            self._gestor.liberar(init_value)

        elif arg["type"] == 'id':
            if self.sim_table[arg["result"][1:-1]]['type'] == 'text':
                for i, ch in enumerate(self.sim_table[arg["result"][1:-1]]['value']):
                    if i == 0:
                        self.data.append(f"{name} : '{ch}'")
                    else:
                        self.data.append(f"{name}{i} : '{ch}'")
            else:
                self.data.append(f"{name} : 0")
                r1 = self._gestor.ocupar()
                n_code.extend([
                    f'MOVD {r1}, {arg["result"]}',
                    f'MOVD [{name}], {r1}'
                ])
                self._gestor.liberar(r1)

        else:

            decl = f'{name} : {init_value}'
            self.data.append(decl)
        
        return n_code

            

    def p_let_with_val(self, p):
        """let_stmt : LET ID COLON type_annot ASSIGN initializer"""

        value = p[6]
        n_code = []

        
        if p[4] in self.sim_table.keys() and self.sim_table[p[4]]['kind'] == 'mold':
            #{ Personas : {attr: [nom1, nom2, nom3] } }
            for i, atr in enumerate(self.sim_table[p[4]]['attr']): 
                tipo = self.sim_table[atr]['type']
                name = p[2] + '@' + atr
                n_code.extend(self._handle_by_type(name, tipo, p[6][i]))

            p[0] = {
            "code": n_code,
            "result": p[2],
            "sect": '.data'
            }
            return 
    


        if isinstance(value, dict):
            init_value = value["result"]
            code = value["code"]
        else:
            init_value = value
            code = []

        # string -> convertir a arreglo de chars
        if p[4] == "text":
            self.sim_table[p[2]]['len'] = len(init_value)

            for i, ch in enumerate(init_value):
                if i == 0:
                    self.data.append(f"{p[2]} : '{ch}'")
                else:
                    self.data.append(f"{p[2]}{i} : '{ch}'")

        elif 'temp' in value:
            decl = f'{p[2]} : 0'
            self.data.append(decl)
            n_code = [f'MOVD [{p[2]}], {init_value}']
            self._gestor.liberar(init_value)
        
        elif value["type"] == 'id':
            if self.sim_table[value["result"][1:-1]]['type'] == 'text':
                for i, ch in enumerate(self.sim_table[value["result"][1:-1]]['value']):
                    if i == 0:
                        self.data.append(f"{p[2]} : '{ch}'")
                    else:
                        self.data.append(f"{p[2]}{i} : '{ch}'")
            else:
                self.data.append(f"{p[2]} : 0")
                r1 = self._gestor.ocupar()
                n_code = [
                    f'MOVD {r1}, {value["result"]}',
                    f'MOVD [{p[2]}], {r1}'
                ]
                self._gestor.liberar(r1)

        else:

            decl = f'{p[2]} : {init_value}'
            self.data.append(decl)

        p[0] = {
            "code": code + n_code,
            "result": p[2],
            "sect": '.data'
        }

    def p_let_array_1d(self, p):
        """let_stmt : LET ID COLON type_annot LBRACKET expr RBRACKET"""

        length = p[6]

        if isinstance(length, dict):
            res = length["result"]
            length = int(res) if isinstance(res, (int, float)) else self.sim_table[res]["value"]

        # Array de molds: emitir una entrada por (campo × elemento)
        if p[4] in self.sim_table and self.sim_table[p[4]].get('kind') == 'mold':
            fields = self.sim_table[p[4]]['attr']
            for i in range(length):
                suffix = '' if i == 0 else str(i)
                for field in fields:
                    tipo = self.sim_table[field]['type']
                    defecto = self._default_for_type(tipo)
                    self.data.append(f'{p[2]}@{field}{suffix} : {defecto}')
            p[0] = {"code": [], "result": p[2]}
            return

        defecto = 0
        if p[4] == "int":    defecto = 0
        elif p[4] == "float": defecto = 0.0
        elif p[4] == "text":  defecto = "' '"
        elif p[4] == "bool":  defecto = 0

        self.data.append(f'{p[2]} : {defecto}')
        for i in range(1, length):
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

        # Array de molds: cada elemento del initializer es la arg_list de un summon
        if p[4] in self.sim_table and self.sim_table[p[4]].get('kind') == 'mold':
            fields = self.sim_table[p[4]]['attr']
            values = p[9]
            # Un solo summon → values es flat list de args; varios → lista de listas
            if values and not isinstance(values[0], list):
                summon_list = [values]
            else:
                summon_list = values
            for i, summon_args in enumerate(summon_list):
                suffix = '' if i == 0 else str(i)
                for j, field in enumerate(fields):
                    arg = summon_args[j]
                    val = arg['result'] if isinstance(arg, dict) else arg
                    self.data.append(f'{p[2]}@{field}{suffix} : {val}')
            p[0] = {"code": [], "result": p[2]}
            return

        values = p[9]
        self.data.append(f'{p[2]} : {values[0]["result"]}')

        for i in range(1, length):
            try:
                self.data.append(f'{p[2]}{i} : {values[i]["result"]}')
            except Exception:
                self.data.append(f'{p[2]}{i} : 0')

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
            defecto = "' '"
        elif p[4] == "bool":
            defecto = 0

        rows = p[6]
        cols = p[9]

        if isinstance(rows, dict):
            rows = self.sim_table[rows["result"]]["value"]

        if isinstance(cols, dict):
            cols = self.sim_table[cols["result"]]["value"]

        total = rows * cols
        self.data.append(f'{p[2]} : {defecto}')
        for i in range(1, total):
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
        v0 = values[0]["result"] if isinstance(values[0], dict) else values[0]
        self.data.append(f'{p[2]} : {v0}')
        for i in range(1, total):
            vi = values[i]["result"] if isinstance(values[i], dict) else values[i]
            self.data.append(f'{p[2]}{i} : {vi}')

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

    def _deref_if_indirect(self, expr_dict, instrs):
        """Si el resultado del expr es [Rx] (campo de mold en array), carga el valor en Rx."""
        r = expr_dict["result"]
        if isinstance(r, str) and r.startswith('[') and 'reg' in expr_dict and r == f'[{expr_dict["reg"]}]':
            reg = expr_dict['reg']
            instrs.append(f'MOVD {reg}, {r}')
            return reg
        return r

    def p_set_assign(self, p):
        """set_stmt : SET lvalue ASSIGN expr"""
        instrs = []
        instrs.extend(p[4]['code'])

        rhs_indirect = (
            'temp' in p[4]
            and 'reg' in p[4]
            and p[4]['result'] == f'[{p[4]["reg"]}]'
        )

        if rhs_indirect:
            rhs_reg = p[4]['reg']
            r1 = self._gestor.ocupar()
            instrs.append(f'MOVD {r1}, [{rhs_reg}]')
            self._gestor.liberar(rhs_reg)
        elif 'temp' in p[4]:
            r1 = self._deref_if_indirect(p[4], instrs)
        else:
            r1 = self._gestor.ocupar()
            instrs.append(f'MOVD {r1}, {p[4]["result"]}')

        instrs.extend(p[2]['code'])
        lvalue = p[2]["result"]
        instrs.append(f'MOVD {lvalue}, {r1}')

        self._gestor.liberar(r1)

        if 'temp' in p[2]:
            self._gestor.liberar(p[2]['reg'])

        p[0] = {'code': instrs,
                "result": lvalue
                }


    def p_set_pluseq(self, p):
        """set_stmt : SET lvalue SWEET_PLUS expr"""
        instrs = []
        instrs.extend(p[4]['code'])

        rhs_indirect = (
            'temp' in p[4]
            and 'reg' in p[4]
            and p[4]['result'] == f'[{p[4]["reg"]}]'
        )

        if rhs_indirect:
            rhs_reg = p[4]['reg']
            r1 = self._gestor.ocupar()
            instrs.append(f'MOVD {r1}, [{rhs_reg}]')
            self._gestor.liberar(rhs_reg)
        elif 'temp' in p[4]:
            r1 = self._deref_if_indirect(p[4], instrs)
        else:
            r1 = self._gestor.ocupar()
            instrs.append(f'MOVD {r1}, {p[4]["result"]}')

        instrs.extend(p[2]['code'])
        lvalue = p[2]["result"]
        r2 = self._gestor.ocupar()
        instrs.append(f'MOVD {r2}, {lvalue}')
        instrs.append(f'ADD {r1}, {r2}')
        instrs.append(f'MOVD {lvalue}, {r1}')

        self._gestor.liberar(r1)
        self._gestor.liberar(r2)

        if 'temp' in p[2]:
            self._gestor.liberar(p[2]['reg'])

        p[0] = {'code': instrs,
                "result": lvalue
                }

    # ── Lvalue ────────────────────────────────────────────────────────────

    # ─────────────────────────────────────────────────────────────
    # LVALUES
    # ─────────────────────────────────────────────────────────────

    def p_lvalue_id(self, p):
        """lvalue : ID"""
        p[0] = {
            'code': [],
            "result": f'[{p[1]}]'
        }

    def p_lvalue_ohmy(self, p):
        """lvalue : OHMY"""
        p[0] = None

    def p_lvalue_array_1d(self, p):
        """lvalue : lvalue LBRACKET expr RBRACKET"""

        arr = p[1]["result"]
        arr_name = arr[1:-1]

        instrs = []
        instrs.extend(p[1]['code'])
        instrs.extend(p[3]['code'])

        if 'temp' in p[3]:
            r1 = p[3]["result"]
        else:
            r1 = self._gestor.ocupar()
            instrs.append(f'MOVD {r1}, {p[3]["result"]}')

        arr_sym = self.sim_table.get(arr_name, {})
        arr_type = arr_sym.get('type', '')
        mold_info = self.sim_table.get(arr_type, {})
        is_mold_array = mold_info.get('kind') == 'mold'

        r2 = self._gestor.ocupar()

        if is_mold_array:
            # Stride = número de campos × 8 bytes
            stride = len(mold_info.get('attr', [])) * 8
            first_field = mold_info['attr'][0]
            base_label = f'[{arr_name}@{first_field}]'
            instrs.extend([
                f'MUL {r1}, {stride}',
                f'LEA {r2}, {base_label}',
                f'ADD {r1}, {r2}',
            ])
            self._gestor.liberar(r2)
            p[0] = {
                'code': instrs,
                'result': f'[{r1}]',
                'temp': True,
                'reg': r1,
                'mold_type': arr_type,
            }
        else:
            instrs.extend([
                f'MUL {r1}, 8',
                f'LEA {r2}, {arr}',
                f'ADD {r1}, {r2}',
            ])
            self._gestor.liberar(r2)
            p[0] = {
                'code': instrs,
                'result': f'[{r1}]',
                'temp': True,
                'reg': r1,
            }


    def p_lvalue_member(self, p):
        """lvalue : lvalue DOT ID"""
        if p[1] is None:
            # ohmy.campo → slot global del campo (dentro de un método)
            p[0] = {
                'code': [],
                'result': f'[{p[3]}]',
            }
        elif p[1].get('mold_type'):
            # base dinámica desde arr[i]: sumar offset del campo al puntero
            mold_type = p[1]['mold_type']
            fields = self.sim_table[mold_type]['attr']
            field_idx = fields.index(p[3])
            field_offset = field_idx * 8
            r1 = p[1]['reg']
            instrs = list(p[1]['code'])
            if field_offset > 0:
                instrs.append(f'ADD {r1}, {field_offset}')
            p[0] = {
                'code': instrs,
                'result': f'[{r1}]',
                'temp': True,
                'reg': r1,
            }
        else:
            # instancia estática: instancia@campo
            name_atr = p[1]['result'][1:-1] + '@' + p[3]
            p[0] = {
                'code': p[1].get('code', []),
                'result': f'[{name_atr}]',
            }

    # ── Función ───────────────────────────────────────────────────────────

    def p_func_def(self, p):
        """func_def : FUNC ID LPAREN param_list RPAREN block"""
        #stack pointer in R13
        #for recover 
        temps = []
        for param in p[4]:
            temps.append(f'{param["result"][1:-1]}temp : 0')
        self.data.extend(temps)
        instrs = []
        label = p[2].upper() + ':'


        # Pasar a las globales place holder 
        write_stmts = []
        reg1 = self._gestor.ocupar()
        reg2 = self._gestor.ocupar()
        write_stmts.append(f'POP {reg2}') #guardamos dir ret
        for param in p[4][::-1]:
            
            write_stmts.append(f'MOVD {reg1} , {param["result"]}')
            write_stmts.append(f'MOVD [{param["result"][1:-1]}temp], {reg1}')
            write_stmts.append(f'POP {reg1}')
            write_stmts.append(f'MOVD {param["result"]}, {reg1}')
        write_stmts.append(f'PUSH {reg2}')
        self._gestor.liberar(reg1)
        self._gestor.liberar(reg2)

        free_stmts = [] #stmts para devolver todo a su lugar luego de la recursion
        b_code = p[6]['code']
        reg1 = self._gestor.ocupar()
        for param in p[4][::-1]:
            
            free_stmts.append(f'MOVD {reg1}, [{param["result"][1:-1]}temp]')
            free_stmts.append(f'MOVD {param["result"]}, {reg1}')
        self._gestor.liberar(reg1)

        ret = 'RET'

        instrs.append(label)
        instrs.extend(write_stmts)
        instrs.extend(b_code)
        instrs.extend(free_stmts)
        instrs.append(ret)
        self.funcs.extend(instrs)

    def p_func_def_no_params(self, p):
        """func_def : FUNC ID LPAREN RPAREN block"""
        instrs = []
        label = p[2].upper() + ':'
        b_code = p[5]['code']
        ret = 'RET'
        instrs.append(label)
        instrs.extend(b_code)
        instrs.append(ret)
        self.funcs.extend(instrs)

    def p_param_list_one(self, p):
        """param_list : param"""
        p[0] = [p[1]]

    def p_param_list_many(self, p):
        """param_list : param_list COMMA param"""
        p[0] = p[1] + [p[3]]

    def p_param(self, p):
        """param : ID COLON type_annot"""
        
        decl = f'{p[1]} : 0'
        self.data.append(decl)

        p[0] = {
            "result": f"[{p[1]}]"
        }

    # ── Mold (TDA / clase) ────────────────────────────────────────────────

    def p_mold_def(self, p):
        """mold_def : MOLD ID LBRACE mold_body RBRACE"""
        p[0] = {
            'code' : []
        }

    def p_mold_body_multi(self, p):
        """mold_body : mold_body mold_member"""
        p[0] = {
            'code' : []
        }

    def p_mold_body_empty(self, p):
        """mold_body : empty"""
        p[0] = {
            'code' : []
        }
    def p_mold_member(self, p):
        """mold_member : let_stmt
                       | func_def"""
        p[0] = {
            'code' : []
        }

    # ─────────────────────────────────────────────────────────────
    # IF
    # ─────────────────────────────────────────────────────────────

    def p_if_simple(self, p):
        """if_stmt : IF expr block"""

        end_label  = f"LEND{self.label_count}"

        self.label_count += 1

        cond_code = p[2]['code']
        cond_res  = (p[2]["result"])

        block_code = p[3]['code']

        instr = []

        instr.extend(cond_code)

        r_cond = cond_res
        _alloc = False
        if isinstance(cond_res, str) and cond_res.startswith('['):
            r_cond = self._gestor.ocupar()
            instr.append(f'MOVD {r_cond}, {cond_res}')
            _alloc = True
        instr.extend([
            f'CMPZ {r_cond}',
            f'JZ {end_label}'
        ])
        if _alloc:
            self._gestor.liberar(r_cond)

        instr.extend(block_code)

        instr.extend([
            f'JMP {end_label}',
            f'{end_label}:'
        ])
        if 'temp' in p[2]:
            self._gestor.liberar(p[2]["result"])
        p[0] = {
            'code': instr
        }

    
    def p_if_otherwise(self, p):
        """if_stmt : IF expr block OTHERWISE block"""

        else_label = f"LELSE{self.label_count}"
        end_label  = f"LEND{self.label_count}"

        self.label_count += 1

        cond_code = p[2]['code']
        cond_res  = (p[2]["result"])

        then_code = p[3]['code']
        else_code = p[5]['code']

        instr = []

        instr.extend(cond_code)

        r_cond = cond_res
        _alloc = False
        if isinstance(cond_res, str) and cond_res.startswith('['):
            r_cond = self._gestor.ocupar()
            instr.append(f'MOVD {r_cond}, {cond_res}')
            _alloc = True
        instr.extend([
            f'CMPZ {r_cond}',
            f'JZ {else_label}'
        ])
        if _alloc:
            self._gestor.liberar(r_cond)

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

        start_label = f"LWHILE_START{self.label_count}"
        end_label   = f"LWHILE_END{self.label_count}"

        self.label_count += 1

        cond_code = p[2]["code"]
        cond_reg  = (p[2]["result"])

        body_code = p[3]["code"]

        code = []

        code.append(f"{start_label}:")

        code.extend(cond_code)

        r_cond = cond_reg
        _alloc = False
        if isinstance(cond_reg, str) and cond_reg.startswith('['):
            r_cond = self._gestor.ocupar()
            code.append(f'MOVD {r_cond}, {cond_reg}')
            _alloc = True
        code.append(f"CMPZ {r_cond}")
        code.append(f"JZ {end_label}")
        if _alloc:
            self._gestor.liberar(r_cond)

        code.extend(body_code)

        code.append(f"JMP {start_label}")

        code.append(f"{end_label}:")

        if 'temp' in p[2]:
            self._gestor.liberar(p[2]["result"])
        p[0] = {
            "code": code
        }
    # ── for ───────────────────────────────────────────────────────────────

    def p_for(self, p):
        """for_stmt : FOR LPAREN for_init COMMA expr COMMA for_update RPAREN block"""

        start_label = f"LFOR_START{self.label_count}"
        end_label   = f"LFOR_END{self.label_count}"

        self.label_count += 1

        init_code = p[3]["code"]

        cond_code = p[5]["code"]
        cond_reg  = (p[5]["result"])

        update_code = p[7]["code"]

        body_code = p[9]["code"]

        code = []

        code.extend(init_code)

        code.append(f"{start_label}:")

        code.extend(cond_code)

        r_cond = cond_reg
        _alloc = False
        if isinstance(cond_reg, str) and cond_reg.startswith('['):
            r_cond = self._gestor.ocupar()
            code.append(f'MOVD {r_cond}, {cond_reg}')
            _alloc = True
        code.append(f"CMPZ {r_cond}")
        code.append(f"JZ {end_label}")
        if _alloc:
            self._gestor.liberar(r_cond)

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
            "result": [p[2]]
        }

    # for_update: set simple, expresión, o vacío
    def p_for_update_set_assign(self, p):
        """for_update : SET lvalue ASSIGN expr"""

        instrs = []
        instrs.extend(p[4]['code'])
        instrs.extend(p[2]['code'])    

        if 'temp' in p[4]:
            n_value = p[4]["result"]
            r1 = p[4]["result"]
        else:
            n_value = p[4]["result"]
            r1 = self._gestor.ocupar()
            instrs.append(
                f'MOVD {r1}, {n_value}'
            )
        lvalue = p[2]["result"]
        instrs.append(f'MOVD {lvalue}, {r1}')
        
        self._gestor.liberar(r1)

        if 'temp' in p[2]:
            self._gestor.liberar(p[2]['reg'])

        p[0] = {'code': instrs,
                "result":lvalue
                }

    def p_for_update_set_pluseq(self, p):
        """for_update : SET lvalue SWEET_PLUS expr"""

        instrs = []
        instrs.extend(p[4]['code'])
        instrs.extend(p[2]['code'])    

        if 'temp' in p[4]:
            n_value = p[4]["result"]
            r1 = p[4]["result"]
        else:
            n_value = p[4]["result"]
            r1 = self._gestor.ocupar()
            instrs.append(
                f'MOVD {r1}, {n_value}'
            )
        lvalue = p[2]["result"]
        r2 = self._gestor.ocupar()
        instrs.append(f'MOVD {r2}, {lvalue}')
        instrs.append(f'ADD {r1}, {r2}')
        instrs.append(f'MOVD {lvalue}, {r1}')
        
        self._gestor.liberar(r1)
        self._gestor.liberar(r2)

        if 'temp' in p[2]:
            self._gestor.liberar(p[2]['reg'])

        p[0] = {'code': instrs,
                "result":lvalue
                }

    def p_for_update_expr(self, p):
        """for_update : expr"""
        p[0] = p[1]

    # ── Sentencias simples ────────────────────────────────────────────────

    def p_deliver_val(self, p):
        """deliver_stmt : DELIVER expr"""
        instrs = list(p[2].get('code', []))
        result = self._deref_if_indirect(p[2], instrs) if 'temp' in p[2] else p[2]["result"]
        instrs.extend([f'MOVD R1, {result}', 'RET'])
        p[0] = {'code': instrs}

    def p_deliver_nothing(self, p):
        """deliver_stmt : DELIVER"""
        p[0] = {
            'code': ['RET']
        }

    def p_show(self, p):
        """show_stmt : SHOW expr"""
        # Incluir el código de cálculo de la expresión (ej: MUL, LEA, ADD para arrays)
        instrs = list(p[2].get('code', []))

        result = p[2]["result"]
        key = result[1:-1] if isinstance(result, str) and result.startswith('[') else str(result)

        if key in self.sim_table:
            tipo_expr = self.sim_table[key]["type"]
        else:
            t = p[2].get('type', 'int')
            tipo_expr = t if t != 'id' else 'int'

        if tipo_expr == "int":
            tipo = 0
            size = 1
        elif tipo_expr == "float":
            tipo = 1
            size = 1
        elif tipo_expr == "text":
            tipo = 2
            size = self.sim_table.get(key, {}).get('len', 1)
        elif tipo_expr == "bool":
            tipo = 3
            size = 1
        else:
            tipo = 0
            size = 1

        # Cuando la dirección está en un registro (resultado de acceso dinámico a mold
        # array), usar MOVD para copiar el registro; para etiquetas, usar LEA normalmente
        if p[2].get('temp') and p[2].get('reg'):
            addr_instr = f'MOVD R11, {p[2]["reg"]}'
        else:
            addr_instr = f'LEA R11, {result}'

        instrs.extend([
            f'MOVD R10, {tipo}',
            addr_instr,
            f'MOVD R12, {size}',
            f'INTR 0',
        ])

        # Liberar el registro temporal una vez usado
        if p[2].get('temp') and p[2].get('reg'):
            self._gestor.liberar(p[2]['reg'])

        p[0] = {
            'code': instrs,
            "result": 1
        }

    def p_oops(self, p):
        """oops_stmt : OOPS expr"""
        p[0] = None

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

        
        instrs = []
        instrs.extend(left_code)
        instrs.extend(right_code)

        if 'temp' in p[1]:
            r1 = self._deref_if_indirect(p[1], instrs)
        else:
            op1 = p[1]["result"]
            r1 = self._gestor.ocupar()
            instrs.append(f'MOVD {r1}, {op1}')

        is_float = (
            p[1].get('type') == 'float' or
            p[3].get('type') == 'float'
        )
        op2 = p[3]["result"]

        if p[2] == '+':

            if is_float:
                instrs.append(f'FPADD {r1}, {op2}')
            else:
                instrs.append(f'ADD {r1}, {op2}')

        elif p[2] == '-':

            if is_float:
                instrs.append(f'FPSUB {r1}, {op2}')
            else:
                instrs.append(f'SUB {r1}, {op2}')

        elif p[2] == '*':

            if is_float:
                instrs.append(f'FPMUL {r1}, {op2}')
            else:
                instrs.append(f'MUL {r1}, {op2}')

        elif p[2] == '/':

            if is_float:
                instrs.append(f'FPDIV {r1}, {op2}')
            else:
                instrs.append(f'DIV {r1}, {op2}')

        elif p[2] == '%':

            if is_float:
                instrs.append(f'FPMOD {r1}, {op2}')
            else:
                instrs.append(f'MOD {r1}, {op2}')
        
        if 'temp' in p[3]:
            self._gestor.liberar(p[3]["result"])

        p[0] = {
            'code': instrs,
            "result": f'{r1}',
            'temp': True,
            'type': p[1]['type']
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
        instrs = []
        instrs.extend(left_code)
        instrs.extend(right_code)

        true_label = f"LTRUE{self.label_count}"
        false_label  = f"LFALSE{self.label_count}"
        self.label_count += 1

        
        if 'temp' in p[1]:
            r1 = self._deref_if_indirect(p[1], instrs)
        else:
            op1 = p[1]["result"]
            r1 = self._gestor.ocupar()
            instrs.append(f'MOVD {r1}, {op1}')

        op2 = p[3]["result"]

        instrs.append(f'CMP {r1}, {op2}')

        if p[2] == '==':   instrs.append(f'JZ {true_label}')
        elif p[2] == '!=': instrs.append(f'JNZ {true_label}')
        elif p[2] == '<':  instrs.append(f'JL {true_label}')
        elif p[2] == '>':  instrs.append(f'JG {true_label}')
        elif p[2] == '<=': instrs.append(f'JLE {true_label}')
        elif p[2] == '>=': instrs.append(f'JGE {true_label}')

        instrs.extend([
            f'MOVD {r1}, 0',
            f'JMP {false_label}',
            f'{true_label}:',
            f'MOVD {r1}, 1',
            f'{false_label}:'
        ])

        if 'temp' in p[3]:
            self._gestor.liberar(p[3]["result"])


        p[0] = {'code': instrs, 
                "result": f'{r1}',
                'type': "bool",
                'temp': True
                }


    # ─────────────────────────────────────────────────────────────
    # LOGICAL
    # ─────────────────────────────────────────────────────────────

    def p_expr_and(self, p):
        """expr : expr AND expr"""

        left_code  = p[1]['code']
        right_code = p[3]['code']

        instrs = []

        instrs.extend(left_code)
        instrs.extend(right_code)

        #Revisamos si ya se hace uso de algun registro temp
        if 'temp' in p[1]:
            op1 = p[1]["result"]
            r1 = p[1]["result"]
        else:
            op1 = p[1]["result"]
            r1 = self._gestor.ocupar()
            instrs.append(
                f'MOVD {r1}, {op1}'
            )

        op2 = (p[3]["result"])

        
        instrs.extend([
            f'AND {r1}, {op2}'
        ])

        #Liberamos el registro del segundo operando
        if 'temp' in p[3]:
            self._gestor.liberar(p[3]["result"])

        p[0] = {
            'code': instrs,
            "result": f'{r1}',
            'type': "bool",
            'temp': True
        }


    def p_expr_or(self, p):
        """expr : expr OR expr"""

        left_code  = p[1]['code']
        right_code = p[3]['code']

        instrs = []

        instrs.extend(left_code)
        instrs.extend(right_code)

        #Revisamos si ya se hace uso de algun registro temp
        if 'temp' in p[1]:
            op1 = p[1]["result"]
            r1 = p[1]["result"]
        else:
            op1 = p[1]["result"]
            r1 = self._gestor.ocupar()
            instrs.append(
                f'MOVD {r1}, {op1}'
            )

        op2 = (p[3]["result"])

        
        instrs.extend([
            f'OR {r1}, {op2}'
        ])

        #Liberamos el registro del segundo operando
        if 'temp' in p[3]:
            self._gestor.liberar(p[3]["result"])

        p[0] = {
            'code': instrs,
            "result": f'{r1}',
            'type': "bool",
            'temp': True
        }


    def p_expr_xor(self, p):
        """expr : expr XOR expr"""

        left_code  = p[1]['code']
        right_code = p[3]['code']

        instrs = []

        instrs.extend(left_code)
        instrs.extend(right_code)

        #Revisamos si ya se hace uso de algun registro temp
        if 'temp' in p[1]:
            op1 = p[1]["result"]
            r1 = p[1]["result"]
        else:
            op1 = p[1]["result"]
            r1 = self._gestor.ocupar()
            instrs.append(
                f'MOVD {r1}, {op1}'
            )

        op2 = (p[3]["result"])

        
        instrs.extend([
            f'XOR {r1}, {op2}'
        ])

        #Liberamos el registro del segundo operando
        if 'temp' in p[3]:
            self._gestor.liberar(p[3]["result"])

        p[0] = {
            'code': instrs,
            "result": f'{r1}',
            'type': "bool",
            'temp': True
        }


    def p_expr_not(self, p):
        """expr : NOT expr"""

        prev_code  = p[2]['code']

        instrs = []

        instrs.extend(prev_code)

        #Revisamos si ya se hace uso de algun registro temp
        if 'temp' in p[2]:
            op1 = p[2]["result"]
            r1 = p[2]["result"]
        else:
            op1 = p[2]["result"]
            r1 = self._gestor.ocupar()
            instrs.append(
                f'MOVD {r1}, {op1}'
            )

        instrs.extend([
            f'NOT {r1}'
        ])

        p[0] = {
            'code': instrs,
            "result": f'{r1}',
            'type': "bool",
            'temp': True
        }




    # ─────────────────────────────────────────────────────────────
    # UMINUS
    # ─────────────────────────────────────────────────────────────

    def p_expr_uminus(self, p):
        """expr : MINUS expr %prec UMINUS"""

        prev_code  = p[2]['code']

        instrs = []

        instrs.extend(prev_code)

        #Revisamos si ya se hace uso de algun registro temp
        if 'temp' in p[2]:
            op1 = p[2]["result"]
            r1 = p[2]["result"]
        else:
            op1 = p[2]["result"]
            r1 = self._gestor.ocupar()
            instrs.append(
                f'MOVD {r1}, {op1}'
            )
    

        if p[2]['type'] == 'float':
            instrs.append(f'FPMUL {r1}, -1.0')
        else:
            instrs.append(f'MUL {r1}, -1')

        p[0] = {
            'code': instrs,
            "result": f'{r1}',
            'type': p[2]['type'],
            'temp' : True
        }


    # Acceso a arreglo
    def p_expr_index(self, p):
        """expr : expr LBRACKET expr RBRACKET"""
        arr_code = p[1]['code']
        ind_code = p[3]['code']

        instrs = []
        instrs.extend(arr_code)
        instrs.extend(ind_code)

        arr = p[1]["result"]
        arr_name = arr[1:-1]

        if 'temp' in p[3]:
            r1 = p[3]["result"]
        else:
            r1 = self._gestor.ocupar()
            instrs.append(f'MOVD {r1}, {p[3]["result"]}')

        arr_sym = self.sim_table.get(arr_name, {})
        arr_type = arr_sym.get('type', '')
        mold_info = self.sim_table.get(arr_type, {})
        is_mold_array = mold_info.get('kind') == 'mold'

        r2 = self._gestor.ocupar()

        if is_mold_array:
            # Devuelve puntero al inicio del elemento; .campo añadirá el offset
            stride = len(mold_info.get('attr', [])) * 8
            first_field = mold_info['attr'][0]
            base_label = f'[{arr_name}@{first_field}]'
            instrs.extend([
                f'MUL {r1}, {stride}',
                f'LEA {r2}, {base_label}',
                f'ADD {r1}, {r2}',
            ])
            self._gestor.liberar(r2)
            p[0] = {
                'code': instrs,
                'result': f'[{r1}]',
                'temp': True,
                'mold_type': arr_type,
                'reg': r1,
                'type': arr_type,
            }
        else:
            instrs.extend([
                f'MUL {r1}, 8',
                f'LEA {r2}, {arr}',
                f'ADD {r1}, {r2}',
                f'MOVD {r2}, [{r1}]',
            ])
            self._gestor.liberar(r1)
            p[0] = {
                'code': instrs,
                'result': f'{r2}',
                'temp': True,
                'type': f'{self.sim_table[arr_name]["type"]}',
            }


    # Acceso a miembro / llamada a método
    def p_expr_method_call(self, p):
        """expr : expr DOT ID LPAREN arg_list RPAREN
                | expr DOT ID LPAREN RPAREN"""
        #Llenamos los place-holders con el valor de quien llama
        place_instr = []
        clase = self.sim_table[p[1]['result'][1:-1]]['type']

        r1 = self._gestor.ocupar()

        for atr in self.sim_table[clase]['attr']:
            place_instr.append(f'MOVD {r1}, [{p[1]["result"][1:-1]}@{atr}]')
            place_instr.append(f'MOVD [{atr}], {r1}')

        self._gestor.liberar(r1)

        if len(p) == 7:
            # expr DOT ID LPAREN arg_list RPAREN  →  p[3]=ID, p[5]=arg_list
            instrs = list(place_instr)
            r = self._gestor.ocupar()
            for param in p[5]:
                instrs.append(f'MOVD {r}, {param["result"]}')
                instrs.append(f'PUSH {r}')
            self._gestor.liberar(r)
            instrs.append(f'CALL {p[3].upper()}')
            p[0] = {'code': instrs, "result": 'R1'}
        else:
            # expr DOT ID LPAREN RPAREN  →  p[3]=ID
            p[0] = {'code': place_instr + [f'CALL {p[3].upper()}'], "result": 'R1'}

    def p_expr_member(self, p):
        """expr : expr DOT ID"""
        if p[1].get('mold_type'):
            # base dinámica desde arr[i]: sumar offset del campo al puntero
            mold_type = p[1]['mold_type']
            fields = self.sim_table[mold_type]['attr']
            field_idx = fields.index(p[3])
            field_offset = field_idx * 8
            r1 = p[1]['reg']
            instrs = list(p[1]['code'])
            if field_offset > 0:
                instrs.append(f'ADD {r1}, {field_offset}')
            p[0] = {
                'code': instrs,
                'result': f'[{r1}]',
                'temp': True,
                'reg': r1,
                'type': self.sim_table[p[3]]['type'],
            }
        else:
            # instancia estática: instancia@campo
            name_atr = p[1]['result'][1:-1] + '@' + p[3]
            p[0] = {
                'code': [],
                'result': f'[{name_atr}]',
                'type': self.sim_table[p[3]]['type'],
            }

    # Llamada a función
    def p_expr_call_args(self, p):
        """expr : ID LPAREN arg_list RPAREN"""
        instrs = []
        r = self._gestor.ocupar()
        for param in p[3]:
            ins0 = f'MOVD {r}, {param["result"]}'
            ins1 = f'PUSH {r}'
            instrs.append(ins0)
            instrs.append(ins1)
        r = self._gestor.liberar(r)
        instrs.append(f'CALL {p[1].upper()}')
        
        p[0] = {'code': instrs,
                "result":'R1'}

    def p_expr_call_noargs(self, p):
        """expr : ID LPAREN RPAREN"""
        p[0] = {'code': [f'CALL {p[1].upper()}'],
                "result": 'R1' }

    # summon
    def p_expr_summon_args(self, p):
        """expr : SUMMON ID LPAREN arg_list RPAREN"""

        p[0] = p[4]

    def p_expr_summon_noargs(self, p):
        """expr : SUMMON ID LPAREN RPAREN"""
        p[0] = []

    # ohmy
    def p_expr_ohmy_member(self, p):
        """expr : OHMY DOT ID"""
        p[0] = {
            'code' : [],
            'type' : self.sim_table[p[3]]["type"],
            'result' : f'[{p[3]}]'
        }

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
        sym = self.sim_table.get(p[1], {})
        p[0] = {
            'code': [],
            "result": f'[{p[1]}]',
            'type': sym.get('type', 'id')
        }


    def p_expr_int(self, p):
        """expr : INT_LIT"""

        p[0] = {
            'code': [],
            "result": int(p[1]),
            'type': 'int'
        }


    def p_expr_float(self, p):
        """expr : FLOAT_LIT"""

        p[0] = {
            'code': [],
            "result": float(p[1]),
            'type': 'float'
        }


    def p_expr_string(self, p):
        """expr : STRING"""
        p[0] = {
            'code': [],
            "result": str(p[1]),
            'type': 'text'
        }


    def p_expr_indeed(self, p):
        """expr : INDEED"""

        p[0] = {
            'code': [],
            "result": 1,
            'type': 'bool'
        }


    def p_expr_nope(self, p):
        """expr : NOPE"""

        p[0] = {
            'code': [],
            "result": 0,
            'type': 'bool'
        }


    def p_expr_nothing(self, p):
        """expr : NOTHING"""
        p[0] = {
            'code': [],
            "result": -0.0,
            'type': 'none'
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
        self._gestor = GestorRegistros()
        self.parser = yacc.yacc(
            module=self,
            debug=False,
            write_tables=False,
        )
        self.text = []
        self.data = []
        self.funcs = []
        self.label_count = 0
        self.scope_count = 0
        self.params_id = {} #func: {param:id} 
    def parse(self, codigo: str, metadata) -> tuple[list[str], object]:
        """
        Analiza el código fuente y devuelve (errores, ast).

        Parámetros:
            codigo  -- cadena con el código CacaoScript preprocesado.

        Retorna:
            errores -- lista de strings con mensajes de error léxico+sintáctico.
            ast     -- NodoPrograma raíz del árbol, o None si no se pudo parsear.
        """
        self.text = []
        self.data = []
        self.errors = []
        _, _, _, self.num_table = self._lex.analize(codigo)
        dict_s = AnalizadorSemantico().parse(codigo, metadata)
        self.sim_table = dict_s['symbol_table']
        # Reinicializar el lexer para el parser
        self._lex.lexer.input(codigo)
        self._lex.lexer.lineno = 1
        ast = self.parser.parse(
            lexer=self._lex.lexer,
            tracking=True,
            debug=False
        )
        return self.errors, ast


# Programa de prueba
if __name__ == '__main__':

    a_s = GeneradorCodigo()
 
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
    print(a_s.data)
    print(a_s.text)
