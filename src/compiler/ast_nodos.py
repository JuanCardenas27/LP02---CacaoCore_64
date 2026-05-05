"""
ast_nodos.py
============
Nodos del Árbol de Sintaxis Abstracta (AST) para CacaoScript.
Cada nodo representa una construcción del lenguaje y expone
un método pprint(indent) para visualización legible.
"""


class Nodo:
    """Clase base de todos los nodos del AST."""
    linea: int = 0

    def pprint(self, indent: int = 0) -> str:
        raise NotImplementedError(f"pprint no implementado en {type(self).__name__}")

    def __repr__(self):
        return self.pprint(0)


# ─── Programa ────────────────────────────────────────────────────────────────

class NodoPrograma(Nodo):
    """Raíz del AST: lista de sentencias de nivel superior."""
    def __init__(self, sentencias: list):
        self.sentencias = sentencias

    def pprint(self, indent=0):
        sp = "  " * indent
        hijos = "\n".join(s.pprint(indent + 1) for s in self.sentencias)
        return f"{sp}[Programa]\n{hijos}"


# ─── Declaraciones ───────────────────────────────────────────────────────────

class NodoDeclaracion(Nodo):
    """let ID : tipo [dim1][dim2] [= valor]"""
    def __init__(self, nombre, tipo, dim1=None, dim2=None, valor=None, linea=0):
        self.nombre = nombre
        self.tipo   = tipo
        self.dim1   = dim1
        self.dim2   = dim2
        self.valor  = valor
        self.linea  = linea

    def pprint(self, indent=0):
        sp   = "  " * indent
        dims = ""
        if self.dim1 is not None:
            dims += f"[{self.dim1.pprint()}]"
        if self.dim2 is not None:
            dims += f"[{self.dim2.pprint()}]"
        val = f" = {self.valor.pprint()}" if self.valor is not None else ""
        return f"{sp}Declaracion '{self.nombre}': {self.tipo}{dims}{val}  (l.{self.linea})"


class NodoReasignacion(Nodo):
    """set lvalue (= | +=) expr"""
    def __init__(self, lvalue, op, expr, linea=0):
        self.lvalue = lvalue
        self.op     = op
        self.expr   = expr
        self.linea  = linea

    def pprint(self, indent=0):
        sp = "  " * indent
        return f"{sp}Reasignacion {self.lvalue.pprint()} {self.op} {self.expr.pprint()}  (l.{self.linea})"


# ─── Funciones y Tipos ───────────────────────────────────────────────────────

class NodoFuncion(Nodo):
    """func ID(params) { cuerpo }"""
    def __init__(self, nombre, params, cuerpo, linea=0):
        self.nombre = nombre
        self.params = params   # lista de (id, tipo)
        self.cuerpo = cuerpo
        self.linea  = linea

    def pprint(self, indent=0):
        sp = "  " * indent
        params_str = ", ".join(f"{n}:{t}" for n, t in self.params)
        return (f"{sp}Funcion '{self.nombre}'({params_str})  (l.{self.linea})\n"
                f"{self.cuerpo.pprint(indent + 1)}")


class NodoMold(Nodo):
    """mold ID { miembros }"""
    def __init__(self, nombre, miembros, linea=0):
        self.nombre   = nombre
        self.miembros = miembros
        self.linea    = linea

    def pprint(self, indent=0):
        sp    = "  " * indent
        hijos = "\n".join(m.pprint(indent + 1) for m in self.miembros)
        return f"{sp}Mold '{self.nombre}'  (l.{self.linea})\n{hijos}"


# ─── Control de flujo ────────────────────────────────────────────────────────

class NodoSi(Nodo):
    """if cond block [otherwise block]"""
    def __init__(self, condicion, entonces, sino=None, linea=0):
        self.condicion = condicion
        self.entonces  = entonces
        self.sino      = sino
        self.linea     = linea

    def pprint(self, indent=0):
        sp  = "  " * indent
        res = (f"{sp}Si ({self.condicion.pprint()})  (l.{self.linea})\n"
               f"{self.entonces.pprint(indent + 1)}")
        if self.sino is not None:
            res += f"\n{sp}Otherwise\n{self.sino.pprint(indent + 1)}"
        return res


class NodoMientras(Nodo):
    """asLongAs cond { cuerpo }"""
    def __init__(self, condicion, cuerpo, linea=0):
        self.condicion = condicion
        self.cuerpo    = cuerpo
        self.linea     = linea

    def pprint(self, indent=0):
        sp = "  " * indent
        return (f"{sp}Mientras ({self.condicion.pprint()})  (l.{self.linea})\n"
                f"{self.cuerpo.pprint(indent + 1)}")


class NodoPara(Nodo):
    """for (inicio , condicion , actualizacion) { cuerpo }"""
    def __init__(self, inicio, condicion, actualizacion, cuerpo, linea=0):
        self.inicio        = inicio
        self.condicion     = condicion
        self.actualizacion = actualizacion
        self.cuerpo        = cuerpo
        self.linea         = linea

    def pprint(self, indent=0):
        sp  = "  " * indent
        ini = self.inicio.pprint() if self.inicio is not None else "ε"
        upd = self.actualizacion.pprint() if self.actualizacion is not None else "ε"
        return (f"{sp}Para ({ini} ; {self.condicion.pprint()} ; {upd})  (l.{self.linea})\n"
                f"{self.cuerpo.pprint(indent + 1)}")


# ─── Sentencias simples ───────────────────────────────────────────────────────

class NodoEntregar(Nodo):
    """deliver [expr]"""
    def __init__(self, expr=None, linea=0):
        self.expr  = expr
        self.linea = linea

    def pprint(self, indent=0):
        sp  = "  " * indent
        val = f" {self.expr.pprint()}" if self.expr is not None else ""
        return f"{sp}Entregar{val}  (l.{self.linea})"


class NodoMostrar(Nodo):
    """show expr"""
    def __init__(self, expr, linea=0):
        self.expr  = expr
        self.linea = linea

    def pprint(self, indent=0):
        sp = "  " * indent
        return f"{sp}Mostrar {self.expr.pprint()}  (l.{self.linea})"


class NodoOops(Nodo):
    """oops expr"""
    def __init__(self, expr, linea=0):
        self.expr  = expr
        self.linea = linea

    def pprint(self, indent=0):
        sp = "  " * indent
        return f"{sp}Oops {self.expr.pprint()}  (l.{self.linea})"


class NodoPreprocesador(Nodo):
    """Referencia de preprocesador (.import / .extern)"""
    def __init__(self, tipo, valor, linea=0):
        self.tipo  = tipo   # 'import' | 'extern'
        self.valor = valor
        self.linea = linea

    def pprint(self, indent=0):
        sp = "  " * indent
        return f"{sp}Prepro[{self.tipo}] '{self.valor}'  (l.{self.linea})"


# ─── Bloque ───────────────────────────────────────────────────────────────────

class NodoBloque(Nodo):
    """{ sentencias }"""
    def __init__(self, sentencias, linea=0):
        self.sentencias = sentencias
        self.linea      = linea

    def pprint(self, indent=0):
        sp    = "  " * indent
        hijos = "\n".join(s.pprint(indent) for s in self.sentencias)
        return f"{sp}Bloque\n{hijos}" if hijos else f"{sp}Bloque (vacío)"


# ─── Expresiones ─────────────────────────────────────────────────────────────

class NodoBinario(Nodo):
    """expr OP expr"""
    def __init__(self, op, izq, der, linea=0):
        self.op    = op
        self.izq   = izq
        self.der   = der
        self.linea = linea

    def pprint(self, indent=0):
        sp = "  " * indent
        return f"({self.izq.pprint()} {self.op} {self.der.pprint()})"


class NodoUnario(Nodo):
    """OP expr  (negación, not)"""
    def __init__(self, op, expr, linea=0):
        self.op    = op
        self.expr  = expr
        self.linea = linea

    def pprint(self, indent=0):
        return f"({self.op}{self.expr.pprint()})"


class NodoLlamada(Nodo):
    """ID(args) o expr.ID(args)"""
    def __init__(self, func, args, linea=0):
        self.func  = func   # str o NodoAccesoMiembro
        self.args  = args
        self.linea = linea

    def pprint(self, indent=0):
        func_str = self.func if isinstance(self.func, str) else self.func.pprint()
        args_str = ", ".join(a.pprint() for a in self.args)
        return f"Llamada {func_str}({args_str})"


class NodoAccesoMiembro(Nodo):
    """expr . ID"""
    def __init__(self, obj, miembro, linea=0):
        self.obj     = obj
        self.miembro = miembro
        self.linea   = linea

    def pprint(self, indent=0):
        obj_str = self.obj if isinstance(self.obj, str) else self.obj.pprint()
        return f"({obj_str}.{self.miembro})"


class NodoAccesoArreglo(Nodo):
    """expr[idx] o expr[idx1][idx2]"""
    def __init__(self, arreglo, indices, linea=0):
        self.arreglo = arreglo   # str o nodo
        self.indices = indices   # lista de nodos
        self.linea   = linea

    def pprint(self, indent=0):
        base = self.arreglo if isinstance(self.arreglo, str) else self.arreglo.pprint()
        idx  = "".join(f"[{i.pprint()}]" for i in self.indices)
        return f"{base}{idx}"


class NodoSummon(Nodo):
    """summon ID(args)"""
    def __init__(self, clase, args, linea=0):
        self.clase = clase
        self.args  = args
        self.linea = linea

    def pprint(self, indent=0):
        args_str = ", ".join(a.pprint() for a in self.args)
        return f"Summon {self.clase}({args_str})"


class NodoListaValores(Nodo):
    """Inicializador de arreglo: v1, v2, ..., vN"""
    def __init__(self, valores, linea=0):
        self.valores = valores
        self.linea   = linea

    def pprint(self, indent=0):
        return "[" + ", ".join(v.pprint() for v in self.valores) + "]"


# ─── Literales e identificadores ─────────────────────────────────────────────

class NodoID(Nodo):
    def __init__(self, nombre, linea=0):
        self.nombre = nombre
        self.linea  = linea

    def pprint(self, indent=0):
        return str(self.nombre)


class NodoEntero(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea

    def pprint(self, indent=0):
        return str(self.valor)


class NodoFlotante(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea

    def pprint(self, indent=0):
        return str(self.valor)


class NodoCadena(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea

    def pprint(self, indent=0):
        return f'"{self.valor}"'


class NodoBooleano(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea

    def pprint(self, indent=0):
        return "indeed" if self.valor else "nope"


class NodoNada(Nodo):
    def __init__(self, linea=0):
        self.linea = linea

    def pprint(self, indent=0):
        return "nothing"


class NodoOhmy(Nodo):
    """Referencia al objeto actual (self)"""
    def __init__(self, linea=0):
        self.linea = linea

    def pprint(self, indent=0):
        return "ohmy"
