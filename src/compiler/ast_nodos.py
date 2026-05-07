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
        "NodoID": "ID",
        "NodoEntero": "INT_LIT",
        "NodoFlotante": "FLOAT_LIT",
        "NodoCadena": "STRING",
        "NodoBooleano": "BOOLEAN",
        "NodoNada": "NOTHING",
        "NodoOhmy": "OHMY",
    }

    def render(self, value) -> str:
        return "\n".join(self._render_value(value, prefix="", is_last=True, field_name=None, is_root=True))

    def _render_value(self, value, prefix: str, is_last: bool, field_name: str | None, is_root: bool = False) -> list[str]:
        if value is None:
            return []

        if isinstance(value, Nodo):
            label = self._label_for_node(value)
            if field_name is not None:
                label = f"{field_name}: {label}"
            connector = "" if is_root else ("└── " if is_last else "├── ")
            lines = [f"{prefix}{connector}{label}"]
            child_prefix = "" if is_root else prefix + ("    " if is_last else "│   ")
            fields = [
                (name, child)
                for name, child in value.__dict__.items()
                if not name.startswith("_") and name != "linea" and child is not None
            ]
            for index, (name, child) in enumerate(fields):
                child_is_last = index == len(fields) - 1
                lines.extend(self._render_value(child, child_prefix, child_is_last, name))
            return lines

        if isinstance(value, dict):
            items = [(key, child) for key, child in value.items() if child is not None]
            label = f"{field_name}: dict[{len(items)}]" if field_name is not None else f"dict[{len(items)}]"
            connector = "" if is_root else ("└── " if is_last else "├── ")
            lines = [f"{prefix}{connector}{label}"]
            child_prefix = "" if is_root else prefix + ("    " if is_last else "│   ")
            for index, (key, child) in enumerate(items):
                child_is_last = index == len(items) - 1
                lines.extend(self._render_value(child, child_prefix, child_is_last, f"[{key!r}]") )
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
                lines.extend(self._render_value(child, child_prefix, child_is_last, f"[{index}]"))
            return lines

        text = self._scalar_text(value)
        label = f"{field_name}: {text}" if field_name is not None else text
        connector = "" if is_root else ("└── " if is_last else "├── ")
        return [f"{prefix}{connector}{label}"]

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

    def pprint(self, indent: int = 0, is_last: bool = True) -> str:
        return _NodoTreePrinter().render(self)

    def __repr__(self):
        return self.pprint(0)


class NodoPrograma(Nodo):
    """Raíz del AST: lista de sentencias de nivel superior."""
    def __init__(self, sentencias: list):
        self.sentencias = sentencias


class NodoDeclaracion(Nodo):
    """let ID : tipo [dim1][dim2] [= valor]"""
    def __init__(self, nombre, tipo, dim1=None, dim2=None, valor=None, linea=0):
        self.nombre = nombre
        self.tipo = tipo
        self.dim1 = dim1
        self.dim2 = dim2
        self.valor = valor
        self.linea = linea


class NodoReasignacion(Nodo):
    """set lvalue (= | +=) expr"""
    def __init__(self, lvalue, op, expr, linea=0):
        self.lvalue = lvalue
        self.op = op
        self.expr = expr
        self.linea = linea


class NodoFuncion(Nodo):
    """func ID(params) { cuerpo }"""
    def __init__(self, nombre, params, cuerpo, linea=0):
        self.nombre = nombre
        self.params = params
        self.cuerpo = cuerpo
        self.linea = linea


class NodoMold(Nodo):
    """mold ID { miembros }"""
    def __init__(self, nombre, miembros, linea=0):
        self.nombre = nombre
        self.miembros = miembros
        self.linea = linea


class NodoSi(Nodo):
    """if cond block [otherwise block]"""
    def __init__(self, condicion, entonces, sino=None, linea=0):
        self.condicion = condicion
        self.entonces = entonces
        self.sino = sino
        self.linea = linea


class NodoMientras(Nodo):
    """asLongAs cond { cuerpo }"""
    def __init__(self, condicion, cuerpo, linea=0):
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.linea = linea


class NodoPara(Nodo):
    """for (inicio , condicion , actualizacion) { cuerpo }"""
    def __init__(self, inicio, condicion, actualizacion, cuerpo, linea=0):
        self.inicio = inicio
        self.condicion = condicion
        self.actualizacion = actualizacion
        self.cuerpo = cuerpo
        self.linea = linea


class NodoEntregar(Nodo):
    """deliver [expr]"""
    def __init__(self, expr=None, linea=0):
        self.expr = expr
        self.linea = linea


class NodoMostrar(Nodo):
    """show expr"""
    def __init__(self, expr, linea=0):
        self.expr = expr
        self.linea = linea


class NodoOops(Nodo):
    """oops expr"""
    def __init__(self, expr, linea=0):
        self.expr = expr
        self.linea = linea


class NodoBloque(Nodo):
    """{ sentencias }"""
    def __init__(self, sentencias, linea=0):
        self.sentencias = sentencias
        self.linea = linea


class NodoBinario(Nodo):
    """expr OP expr"""
    def __init__(self, op, izq, der, linea=0):
        self.op = op
        self.izq = izq
        self.der = der
        self.linea = linea


class NodoUnario(Nodo):
    """OP expr  (negación, not)"""
    def __init__(self, op, expr, linea=0):
        self.op = op
        self.expr = expr
        self.linea = linea


class NodoLlamada(Nodo):
    """ID(args) o expr.ID(args)"""
    def __init__(self, func, args, linea=0):
        self.func = func
        self.args = args
        self.linea = linea


class NodoAccesoMiembro(Nodo):
    """expr . ID"""
    def __init__(self, obj, miembro, linea=0):
        self.obj = obj
        self.miembro = miembro
        self.linea = linea


class NodoAccesoArreglo(Nodo):
    """expr[idx] o expr[idx1][idx2]"""
    def __init__(self, arreglo, indices, linea=0):
        self.arreglo = arreglo
        self.indices = indices
        self.linea = linea


class NodoSummon(Nodo):
    """summon ID(args)"""
    def __init__(self, clase, args, linea=0):
        self.clase = clase
        self.args = args
        self.linea = linea


class NodoListaValores(Nodo):
    """Inicializador de arreglo: v1, v2, ..., vN"""
    def __init__(self, valores, linea=0):
        self.valores = valores
        self.linea = linea


class NodoID(Nodo):
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
