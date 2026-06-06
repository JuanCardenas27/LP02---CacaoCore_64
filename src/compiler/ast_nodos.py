"""
ast_nodos.py
============
Nodos del Árbol de Sintaxis Abstracta (AST) para CacaoScript.
Cada nodo representa una construcción del lenguaje; la impresión del árbol
se resuelve en un renderizador genérico para mantener los nodos atómicos.
"""


class _NodoTreePrinter:
    """Renderizador genérico del AST en formato de árbol."""

    _LABELS = {
        "NodoPrograma": "program",
        "NodoDeclaracion": "let_stmt",
        "NodoDimensiones": "dims",
        "NodoReasignacion": "set_stmt",
        "NodoFuncion": "func_def",
        "NodoMold": "mold_def",
        "NodoSi": "if_stmt",
        "NodoMientras": "while_stmt",
        "NodoPara": "for_stmt",
        "NodoEntregar": "deliver_stmt",
        "NodoMostrar": "show_stmt",
        "NodoOops": "oops_stmt",
        "NodoBloque": "block",
        "NodoBinario": "expr_binop",
        "NodoUnario": "expr_unary",
        "NodoLlamada": "expr_call",
        "NodoAccesoMiembro": "expr_member",
        "NodoAccesoArreglo": "expr_index",
        "NodoSummon": "expr_summon",
        "NodoListaValores": "value_list",
        "NodoParametro": "param",
        "NodoID": "ID",
        "NodoEntero": "INT_LIT",
        "NodoFlotante": "FLOAT_LIT",
        "NodoCadena": "STRING",
        "NodoBooleano": "BOOLEAN",
        "NodoNada": "NOTHING",
        "NodoOhmy": "OHMY",
        "NodoTerminal": "TERMINAL",
    }

    def render(self, value) -> str:
        return "\n".join(self._render_value(value, prefix="", is_last=True, field_name=None, is_root=True, seen=set()))

    def _render_value(self, value, prefix: str, is_last: bool, field_name: str | None, is_root: bool = False, seen=None) -> list[str]:
        if value is None:
            return []

        if seen is None:
            seen = set()

        if isinstance(value, (Nodo, dict, list, tuple)):
            value_id = id(value)
            if value_id in seen:
                connector = "" if is_root else ("└── " if is_last else "├── ")
                return [f"{prefix}{connector}{self._compact_ref_label(value, field_name)}"]
            seen.add(value_id)

        if isinstance(value, Nodo):
            if type(value).__name__ == 'NodoTerminal':
                label = f'"{value.valor}"'
                if field_name is not None:
                    label = f"{field_name}: {label}"
                connector = "" if is_root else ("└── " if is_last else "├── ")
                return [f"{prefix}{connector}{label}"]

            label = self._label_for_node(value)
            if field_name is not None:
                label = f"{field_name}: {label}"
            connector = "" if is_root else ("└── " if is_last else "├── ")
            lines = [f"{prefix}{connector}{label}"]
            child_prefix = "" if is_root else prefix + ("    " if is_last else "│   ")
            fields = [
                (name, child)
                for name, child in value.__dict__.items()
                if not name.startswith("_")
                and name not in {"linea", "semantic_info", "tipo_semantico", "tipo_decl"}
                and child is not None
            ]
            for index, (name, child) in enumerate(fields):
                child_is_last = index == len(fields) - 1
                lines.extend(self._render_value(child, child_prefix, child_is_last, name, seen=seen))
            return lines

        if isinstance(value, dict):
            items = [(key, child) for key, child in value.items() if child is not None]
            label = f"{field_name}: dict[{len(items)}]" if field_name is not None else f"dict[{len(items)}]"
            connector = "" if is_root else ("└── " if is_last else "├── ")
            lines = [f"{prefix}{connector}{label}"]
            child_prefix = "" if is_root else prefix + ("    " if is_last else "│   ")
            for index, (key, child) in enumerate(items):
                child_is_last = index == len(items) - 1
                lines.extend(self._render_value(child, child_prefix, child_is_last, f"[{key!r}]", seen=seen))
            return lines

        if isinstance(value, (list, tuple)):
            kind = "list" if isinstance(value, list) else "tuple"
            elements = [(index, child) for index, child in enumerate(value) if child is not None]
            label = f"{field_name}: {kind}[{len(elements)}]" if field_name is not None else f"{kind}[{len(elements)}]"
            connector = "" if is_root else ("└── " if is_last else "├── ")
            lines = [f"{prefix}{connector}{label}"]
            child_prefix = "" if is_root else prefix + ("    " if is_last else "│   ")
            for pos, (index, child) in enumerate(elements):
                child_is_last = pos == len(elements) - 1
                lines.extend(self._render_value(child, child_prefix, child_is_last, f"[{index}]", seen=seen))
            return lines

        text = self._scalar_text(value)
        label = f"{field_name}: {text}" if field_name is not None else text
        connector = "" if is_root else ("└── " if is_last else "├── ")
        return [f"{prefix}{connector}{label}"]

    def _compact_ref_label(self, value, field_name: str | None):
        if isinstance(value, dict):
            base = f"dict[{len(value)}]"
        elif isinstance(value, list):
            base = f"list[{len(value)}]"
        elif isinstance(value, tuple):
            base = f"tuple[{len(value)}]"
        elif isinstance(value, Nodo):
            base = self._label_for_node(value)
        else:
            base = type(value).__name__
        return f"{field_name}: ↩ {base}" if field_name is not None else f"↩ {base}"

    def _label_for_node(self, node) -> str:
        return self._LABELS.get(type(node).__name__, type(node).__name__)

    def _scalar_text(self, value) -> str:
        if value is None:
            return "None"
        if isinstance(value, str):
            return repr(value)
        return str(value)


class Nodo:
    """Clase base de todos los nodos del AST."""

    linea: int = 0
    _allows_symbol = False

    def pprint(self, indent: int = 0, is_last: bool = True) -> str:
        return _NodoTreePrinter().render(self)

    def __repr__(self):
        return self.pprint(0)

    def set_type(self, tipo, dims: int = 0):
        if isinstance(getattr(self, 'tipo', None), Nodo):
            self.tipo_semantico = tipo
        else:
            self.tipo = tipo
        self.dims = dims
        return self

    def _compact_params_info(self, params):
        compact = []
        for param in params:
            if not isinstance(param, dict):
                continue
            param_info = {}
            if param.get('name') is not None:
                param_info['name'] = param.get('name')
            if param.get('type') is not None:
                param_info['type'] = param.get('type')
            if param.get('dims', 0):
                param_info['dims'] = param.get('dims', 0)
            if param_info:
                compact.append(param_info)
        return compact

    def merge_symbol_metadata(self, symbol):
        if not getattr(self, '_allows_symbol', False):
            return self
        if not isinstance(symbol, dict):
            return self

        kind = symbol.get('kind')
        if kind is not None:
            self.kind = kind

        scope_id = symbol.get('scope_id')
        if scope_id is not None:
            self.scope_id = scope_id

        return_type = symbol.get('return_type')
        if return_type is not None:
            self.return_type = return_type

        params = symbol.get('params')
        if isinstance(params, list):
            self.params_info = self._compact_params_info(params)

        if hasattr(self, 'symbol'):
            delattr(self, 'symbol')
        return self

    def set_return_type(self, return_type):
        self.return_type = return_type
        return self


class NodoPrograma(Nodo):
    """Raíz del AST: lista de sentencias de nivel superior."""

    def __init__(self, sentencias: list):
        self.sentencias = sentencias


class NodoDeclaracion(Nodo):
    _allows_symbol = True

    """let ID : tipo dims [= valor]"""

    def __init__(self, nombre, tipo, dims=None, valor=None, linea=0):
        self.let_keyword = NodoTerminal('let', linea)
        self.nombre = nombre
        self.colon = NodoTerminal(':', linea)
        self.tipo = tipo if isinstance(tipo, NodoTerminal) else NodoTerminal(tipo, linea)
        self.dims = dims
        self.assign = NodoTerminal('=', linea) if valor is not None else None
        self.valor = valor
        self.linea = linea


class NodoDimensiones(Nodo):
    """[expr][expr]..."""

    def __init__(self, dimensiones, linea=0):
        self.items = []

        for dim in dimensiones:
            self.items.append(NodoTerminal('[', linea))
            self.items.append(dim)
            self.items.append(NodoTerminal(']', linea))

        self.linea = linea


class NodoReasignacion(Nodo):
    """set lvalue (= | +=) expr"""

    def __init__(self, lvalue, op, expr, linea=0):
        self.set_keyword = NodoTerminal('set', linea)
        self.lvalue = lvalue
        self.op = NodoTerminal(op, linea)
        self.expr = expr
        self.linea = linea


class NodoFuncion(Nodo):
    _allows_symbol = True

    """func ID(params) { cuerpo }"""

    def __init__(self, nombre, params, cuerpo, linea=0):
        self.func_keyword = NodoTerminal('func', linea)
        self.nombre = nombre
        self.lparen = NodoTerminal('(', linea)
        self.params = params
        self.rparen = NodoTerminal(')', linea)
        self.cuerpo = cuerpo
        self.linea = linea


class NodoMold(Nodo):
    _allows_symbol = True

    """mold ID { miembros }"""

    def __init__(self, nombre, miembros, linea=0):
        self.mold_keyword = NodoTerminal('mold', linea)
        self.nombre = nombre
        self.lbrace = NodoTerminal('{', linea)
        self.miembros = miembros
        self.rbrace = NodoTerminal('}', linea)
        self.linea = linea


class NodoSi(Nodo):
    """if cond block [otherwise block]"""

    def __init__(self, condicion, entonces, sino=None, linea=0):
        self.if_keyword = NodoTerminal('if', linea)
        self.condicion = condicion
        self.entonces = entonces
        self.otherwise_keyword = NodoTerminal('otherwise', linea) if sino is not None else None
        self.sino = sino
        self.linea = linea


class NodoMientras(Nodo):
    """asLongAs cond { cuerpo }"""

    def __init__(self, condicion, cuerpo, linea=0):
        self.aslongas_keyword = NodoTerminal('asLongAs', linea)
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.linea = linea


class NodoPara(Nodo):
    """for (inicio , condicion , actualizacion) { cuerpo }"""

    def __init__(self, inicio, condicion, actualizacion, cuerpo, linea=0):
        self.for_keyword = NodoTerminal('for', linea)
        self.lparen = NodoTerminal('(', linea)
        self.inicio = inicio
        self.comma1 = NodoTerminal(',', linea)
        self.condicion = condicion
        self.comma2 = NodoTerminal(',', linea)
        self.actualizacion = actualizacion
        self.rparen = NodoTerminal(')', linea)
        self.cuerpo = cuerpo
        self.linea = linea


class NodoEntregar(Nodo):
    """deliver [expr]"""

    def __init__(self, expr=None, linea=0):
        self.deliver_keyword = NodoTerminal('deliver', linea)
        self.expr = expr
        self.linea = linea


class NodoMostrar(Nodo):
    """show expr"""

    def __init__(self, expr, linea=0):
        self.show_keyword = NodoTerminal('show', linea)
        self.expr = expr
        self.linea = linea


class NodoOops(Nodo):
    """oops expr"""

    def __init__(self, expr, linea=0):
        self.oops_keyword = NodoTerminal('oops', linea)
        self.expr = expr
        self.linea = linea


class NodoBloque(Nodo):
    """{ sentencias }"""

    def __init__(self, sentencias, linea=0):
        self.lbrace = NodoTerminal('{', linea)
        self.sentencias = sentencias
        self.rbrace = NodoTerminal('}', linea)
        self.linea = linea


class NodoBinario(Nodo):
    """expr OP expr"""

    def __init__(self, op, izq, der, linea=0):
        self.izq = izq
        self.op = NodoTerminal(op, linea)
        self.der = der
        self.linea = linea


class NodoUnario(Nodo):
    """OP expr  (negación, not)"""

    def __init__(self, op, expr, linea=0):
        self.op = NodoTerminal(op, linea)
        self.expr = expr
        self.linea = linea


class NodoLlamada(Nodo):
    _allows_symbol = True

    """ID(args) o expr.ID(args)"""

    def __init__(self, func, args, linea=0):
        self.func = func
        self.lparen = NodoTerminal('(', linea)
        self.args = args
        self.rparen = NodoTerminal(')', linea)
        self.linea = linea


class NodoAccesoMiembro(Nodo):
    _allows_symbol = True

    """expr . ID"""

    def __init__(self, obj, miembro, linea=0):
        self.obj = obj
        self.dot = NodoTerminal('.', linea)
        self.miembro = miembro
        self.linea = linea


class NodoAccesoArreglo(Nodo):
    """expr[idx] o expr[idx1][idx2]"""

    def __init__(self, arreglo, indices, linea=0):
        self.arreglo = arreglo
        self.brackets_indices = []
        for idx in indices:
            self.brackets_indices.append(NodoTerminal('[', linea))
            self.brackets_indices.append(idx)
            self.brackets_indices.append(NodoTerminal(']', linea))
        self.linea = linea


class NodoSummon(Nodo):
    _allows_symbol = True

    """summon ID(args)"""

    def __init__(self, clase, args, linea=0):
        self.summon_keyword = NodoTerminal('summon', linea)
        self.clase = clase
        self.lparen = NodoTerminal('(', linea)
        self.args = args
        self.rparen = NodoTerminal(')', linea)
        self.linea = linea


class NodoListaValores(Nodo):
    """Inicializador de arreglo: v1, v2, ..., vN"""

    def __init__(self, valores, linea=0):
        self.items = []
        for i, valor in enumerate(valores):
            self.items.append(valor)
            if i < len(valores) - 1:
                self.items.append(NodoTerminal(',', linea))
        self.linea = linea


class NodoParametro(Nodo):
    _allows_symbol = True

    """param ::= ID : type"""

    def __init__(self, nombre, tipo, dims=None, linea=0):
        self.nombre = nombre
        self.colon = NodoTerminal(':', linea)
        self.tipo = tipo if isinstance(tipo, NodoTerminal) else NodoTerminal(tipo, linea)
        self.linea = linea
        self.dims = dims


class NodoID(Nodo):
    _allows_symbol = True

    def __init__(self, nombre, linea=0):
        self.nombre = nombre
        self.linea = linea


class NodoEntero(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea


class NodoFlotante(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea


class NodoCadena(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea


class NodoBooleano(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea


class NodoNada(Nodo):
    def __init__(self, linea=0):
        self.linea = linea


class NodoOhmy(Nodo):
    """Referencia al objeto actual (self)"""

    def __init__(self, linea=0):
        self.linea = linea


class NodoTerminal(Nodo):
    """Nodo terminal: símbolo de puntuación o palabra clave sin contenido semántico."""

    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea
