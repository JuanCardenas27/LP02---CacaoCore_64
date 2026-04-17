
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import ply.lex as lex


RE_INCLUDE_LINE = re.compile(r'#\s*include\b')
RE_DEFINE_LINE = re.compile(r'#\s*define\b')
RE_UNDEF_LINE = re.compile(r'#\s*undef\b')
RE_IFDEF_LINE = re.compile(r'#\s*ifdef\b')
RE_IFNDEF_LINE = re.compile(r'#\s*ifndef\b')
RE_ELSE_LINE = re.compile(r'#\s*else\b')
RE_ENDIF_LINE = re.compile(r'#\s*endif\b')
RE_ERROR_LINE = re.compile(r'#\s*error\b')
RE_WARNING_LINE = re.compile(r'#\s*warning\b')

RE_PARSE_INCLUDE = re.compile(
    r'^\s*#\s*include\s+"([^"]+)"\s*(?:\{([^}]*)\})?\s*(?:(?://|;|#).*)?$'
)
RE_DEFINE_WITH_PARAMS = re.compile(
    r'^([A-Za-z_][A-Za-z0-9_]*)\(([^)]*)\)\s*(.*)'
)
RE_DEFINE_SIMPLE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*(.*)')

IDENT_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
LABEL_RE = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:')

MNEMONICS = {
    'nop','hlt','ret','ei','di','iret','push','pop','int',
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
REGISTER_NAMES = {f"r{i}" for i in range(16)}
RESERVED_WORDS = MNEMONICS | {'data', 'text', 'extern', 'import'}


@dataclass
class SourceLine:
    """Rastrea el origen de cada línea de salida (para mensajes de error)."""
    path: str   
    line: int   


@dataclass
class PreprocessResult:
    """Resultado completo del preprocesado."""
    text: str                   # texto preprocesado listo para el ensamblador
    line_map: List[SourceLine]  # mapa línea-salida → línea-fuente


class PreprocesadorError(Exception):
    """Base de todos los errores del preprocesador."""
    def __init__(self, mensaje: str, archivo: str = None, linea: int = None):
        self.archivo = archivo
        self.linea   = linea
        ubicacion    = f"{archivo}:{linea}" if archivo else "<desconocido>"
        super().__init__(f"[PREPROCESADOR] {ubicacion}: {mensaje}")

class IncludeError(PreprocesadorError):
    """Error al resolver o leer un #include."""
    pass

class MacroError(PreprocesadorError):
    """Error en la definición o expansión de una macro."""
    pass

class CondicionalError(PreprocesadorError):
    """Error en bloques #ifdef / #ifndef / #else / #endif."""
    pass




tokens = (
    'DIR_INCLUDE',    # #include "archivo"
    'DIR_DEFINE',     # #define NOMBRE [valor]
    'DIR_UNDEF',      # #undef NOMBRE
    'DIR_IFDEF',      # #ifdef NOMBRE
    'DIR_IFNDEF',     # #ifndef NOMBRE
    'DIR_ELSE',       # #else
    'DIR_ENDIF',      # #endif
    'DIR_ERROR',      # #error mensaje
    'DIR_WARNING',    # #warning mensaje
    'COMENTARIO_C',   # // comentario
    'COMENTARIO_ASM', # ; comentario
    'NEWLINE',        # salto de línea (para contar líneas)
    'CODIGO',         # cualquier otro texto de código
)

def t_DIR_INCLUDE(t):
    r'\#[ \t]*include[ \t]+"[^"\n]+"'
    return t

def t_DIR_DEFINE(t):
    r'\#[ \t]*define[ \t]+[A-Za-z_][A-Za-z0-9_]*(\([^)]*\))?[^\n]*'
    return t

def t_DIR_UNDEF(t):
    r'\#[ \t]*undef[ \t]+[A-Za-z_][A-Za-z0-9_]*[^\n]*'
    return t

def t_DIR_IFDEF(t):
    r'\#[ \t]*ifdef[ \t]+[A-Za-z_][A-Za-z0-9_]*[^\n]*'
    return t

def t_DIR_IFNDEF(t):
    r'\#[ \t]*ifndef[ \t]+[A-Za-z_][A-Za-z0-9_]*[^\n]*'
    return t

def t_DIR_ELSE(t):
    r'\#[ \t]*else[^\n]*'
    return t

def t_DIR_ENDIF(t):
    r'\#[ \t]*endif[^\n]*'
    return t

def t_DIR_ERROR(t):
    r'\#[ \t]*error[^\n]*'
    return t

def t_DIR_WARNING(t):
    r'\#[ \t]*warning[^\n]*'
    return t

def t_COMENTARIO_C(t):
    r'//[^\n]*'
    return t

def t_COMENTARIO_ASM(t):
    r';[^\n]*'
    return t

def t_NEWLINE(t):
    r'\r?\n'
    t.lexer.lineno += 1
    return t

def t_CODIGO(t):
    r'[^\r\n]+'
    return t

# No ignorar espacios para preservar el texto original
t_ignore = ''

def t_error(t):
    """Carácter no reconocido: se salta silenciosamente."""
    t.lexer.skip(1)



class Macro:
    """Representa una macro definida con #define."""

    def __init__(self, nombre: str, valor: str,
                 parametros: Optional[List[str]] = None):
        self.nombre     = nombre
        self.valor      = valor
        self.parametros = parametros  # None → simple; lista → con parámetros

    def expandir(self, argumentos: Optional[List[str]] = None) -> str:
        """Sustituye los parámetros formales por los argumentos dados."""
        if self.parametros is None:
            return self.valor

        n_esp = len(self.parametros)
        n_rec = len(argumentos) if argumentos else 0
        if argumentos is None or n_rec != n_esp:
            raise MacroError(
                f"Macro '{self.nombre}' espera {n_esp} argumento(s), "
                f"se recibieron {n_rec}"
            )

        resultado = self.valor
        for param, arg in zip(self.parametros, argumentos):
            resultado = re.sub(
                r'\b' + re.escape(param) + r'\b', arg.strip(), resultado
            )
        return resultado

    def __repr__(self) -> str:
        if self.parametros is not None:
            return (f"Macro({self.nombre}"
                    f"({','.join(self.parametros)}) = {self.valor})")
        return f"Macro({self.nombre} = {self.valor})"




class Preprocesador:
    _EXTERN_PLACEHOLDER = "__EXTERN_PLACEHOLDER__"

    def __init__(self,
                 library_dir: Optional[str] = None,
                 max_macro_expansion: int = 50,
                 macros_iniciales: Optional[Dict[str, str]] = None,
                 verbose: bool = False):

        self.library_dir          = self._resolver_library_dir(library_dir)
        self.max_macro_expansion  = max_macro_expansion
        self.verbose              = verbose
        self.advertencias: List[str] = []

        # Estado interno (se reinicia en cada llamada a preprocess)
        self._defines: Dict[str, Macro]    = {}
        self._define_pattern               = None
        self._pila_cond: List[bool]        = []  # bloques condicionales
        self._imports_set: set             = set()
        self._externs_explicit: set        = set()
        self._extern_placeholder_index     = None

        # Construir el lexer PLY (equivalente a compilar el .l en FLEX)
        self._lexer = lex.lex()

        # Tabla de macros predefinidas del CACAO_Core-64
        self._macros_base = self._build_macros_base()
        if macros_iniciales:
            self._macros_base.update({
                k: Macro(k, str(v)) for k, v in macros_iniciales.items()
            })

    
    def _resolver_library_dir(self, library_dir: Optional[str]) -> str:
        if library_dir and os.path.isabs(library_dir):
            return library_dir
        raiz = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..')
        )
        rel = library_dir or os.path.join('src', 'Libraries')
        return os.path.abspath(os.path.join(raiz, rel))

    def _build_macros_base(self) -> Dict[str, Macro]:
        """Macros predefinidas del CACAO_Core-64 (mapa de memoria, registros, etc.)."""
        defs = {
            '__CACAO_CORE64__': '1',
            '__BITS__':         '64',
            '__WORD_SIZE__':    '8',
            # Mapa de memoria (igual que en ram.py)
            'CODE_START':   '0x00001000',
            'CODE_END':     '0x0003FFFF',
            'DATA_START':   '0x00040000',
            'DATA_END':     '0x0007FFFF',
            'HEAP_START':   '0x00080000',
            'HEAP_END':     '0x000BFFFF',
            'STACK_START':  '0x000C0000',
            'STACK_END':    '0x000FFFFF',
            # Registros especiales
            'SP':  'r13',
            'LR':  'r14',
            'ACC': 'r15',
            # Instrucciones codificadas (8 bytes little-endian)
            'NOP': 'F0 FF FF FF FF FF FF FF',
            'HLT': '00 00 00 00 00 00 00 00',
        }
        return {k: Macro(k, v) for k, v in defs.items()}

    # -------------------------------------------------------------------------
    # Utilidades internas
    # -------------------------------------------------------------------------

    def _activo(self) -> bool:
        """True si el bloque condicional actual debe incluirse."""
        return all(self._pila_cond) if self._pila_cond else True

    def _log(self, msg: str):
        if self.verbose:
            print(f"[PREPROCESADOR] {msg}", file=sys.stderr)

    def _advertir(self, msg: str, archivo: str = None, linea: int = None):
        loc     = f"{archivo}:{linea}" if archivo else "<string>"
        entrada = f"[ADVERTENCIA] {loc}: {msg}"
        self.advertencias.append(entrada)
        print(entrada, file=sys.stderr)

    # -------------------------------------------------------------------------
    # Parseo de directivas
    # -------------------------------------------------------------------------

    def _parsear_define(self, raw: str) -> Macro:
        resto = re.sub(r'^\#\s*define\s+', '', raw).strip()

        # Con parámetros: NOMBRE(p1, p2) valor
        m = RE_DEFINE_WITH_PARAMS.match(resto)
        if m:
            nombre = m.group(1)
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            valor  = m.group(3).strip()
            return Macro(nombre, valor, params)

        # Simple: NOMBRE  o  NOMBRE valor
        m = RE_DEFINE_SIMPLE.match(resto)
        if m:
            return Macro(m.group(1), m.group(2).strip() or '1')

        raise MacroError(f"Sintaxis #define inválida: {raw}")

    def _parsear_include(self, raw: str) -> Tuple[str, Optional[List[str]]]:
        """Extrae el nombre de archivo y lista de funciones de #include."""
        m = RE_PARSE_INCLUDE.match(raw)
        if not m:
            raise IncludeError(f"Sintaxis #include inválida: {raw}")

        nombre = m.group(1)
        lista_raw = m.group(2)
        if lista_raw is None:
            return nombre, None

        funciones = [f.strip() for f in lista_raw.split(',') if f.strip()]
        if not funciones:
            raise IncludeError("Lista de funciones vacia en #include")
        return nombre, funciones

    def _parsear_nombre_macro(self, raw: str, directiva: str) -> str:
        """Extrae el nombre de macro de #ifdef / #ifndef / #undef."""
        m = re.match(rf'#\s*{directiva}\s+([A-Za-z_][A-Za-z0-9_]*)', raw)
        if not m:
            raise PreprocesadorError(f"Sintaxis #{directiva} inválida: {raw}")
        return m.group(1)

    # -------------------------------------------------------------------------
    # Expansión de macros
    # -------------------------------------------------------------------------

    def _get_define_pattern(self) -> Optional[re.Pattern]:
       
        simples = {k: v for k, v in self._defines.items()
                   if v.parametros is None and v.valor}
        if not simples:
            return None
        if self._define_pattern is None:
            nombres = sorted(simples.keys(), key=len, reverse=True)
            patron  = r'\b(' + '|'.join(re.escape(n) for n in nombres) + r')\b'
            self._define_pattern = re.compile(patron)
        return self._define_pattern

    def _find_comment_start(self, line: str) -> Optional[int]:
       
        in_single = False
        in_double = False
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            elif not in_single and not in_double:
                if line.startswith('//', i):
                    return i
                if line.startswith('#', i):
                    return i
                if ch == ';':
                    return i
            i += 1
        return None

    def _strip_comment(self, line: str) -> str:
        idx = self._find_comment_start(line)
        return line[:idx] if idx is not None else line

    def _collect_symbol_sets(self, lineas: List[str]) -> Tuple[set, set]:
        defined: set = set()
        referenced: set = set()

        for linea in lineas:
            if not linea or linea == self._EXTERN_PLACEHOLDER:
                continue
            s = linea.strip()
            if not s:
                continue
            s_lower = s.lower()
            if s_lower.startswith('.import') or s_lower.startswith('.extern'):
                continue

            codigo = self._strip_comment(linea)
            if not codigo.strip():
                continue

            m = LABEL_RE.match(codigo)
            if m:
                defined.add(m.group(1).lower())
                codigo = codigo[m.end():]

            for ident in IDENT_RE.findall(codigo):
                ident_l = ident.lower()
                if ident_l in RESERVED_WORDS:
                    continue
                if ident_l in REGISTER_NAMES:
                    continue
                referenced.add(ident_l)

        return defined, referenced

    def _emit_import(self, nombre: str, lineas: List[str],
                     mapa: List[SourceLine], fuente: str, n_linea: int) -> None:
        if nombre in self._imports_set:
            return
        self._imports_set.add(nombre)
        lineas.append(f'.import "{nombre}"')
        mapa.append(SourceLine(path=fuente, line=n_linea))

    def _expandir_macros(self, linea: str) -> str:
  
        idx = self._find_comment_start(linea)
        codigo = linea[:idx] if idx is not None else linea
        comentario = linea[idx:] if idx is not None else ''

        # Paso 1 — macros con parámetros
        for macro in self._defines.values():
            if macro.parametros is not None:
                patron = re.escape(macro.nombre) + r'\(([^)]*)\)'
                def _reemplazar(match, m=macro):
                    args = [a.strip() for a in match.group(1).split(',')]
                    return m.expandir(args)
                codigo = re.sub(patron, _reemplazar, codigo)

        # Paso 2 — macros simples, múltiples pasadas (macros anidadas)
        for _ in range(self.max_macro_expansion):
            patron = self._get_define_pattern()
            if patron is None:
                break
            anterior = codigo
            codigo = patron.sub(
                lambda m: self._defines[m.group(1)].valor, codigo
            )
            if codigo == anterior:
                break
        else:
            raise MacroError("Límite de expansión de macros alcanzado")

        return codigo + comentario


    def _procesar_tokens(self, texto: str, fuente: str) -> Tuple[List[str], List[SourceLine]]:
      
        lineas_salida: List[str]        = []
        mapa_salida:   List[SourceLine] = []

        # Clonar el lexer para aislar estado entre ejecuciones
        lexer = self._lexer.clone()
        lexer.lineno = 1
        lexer.input(texto)

        # Reconstruir líneas lógicas a partir del flujo de tokens PLY
        linea_buf:   List[str] = []
        n_linea_buf: int       = 1
        lineas_logicas: List[Tuple[int, str]] = []

        for tok in lexer:
            if tok.type == 'NEWLINE':
                lineas_logicas.append((n_linea_buf, ''.join(linea_buf)))
                linea_buf    = []
                n_linea_buf  = lexer.lineno
            else:
                linea_buf.append(tok.value)

        if linea_buf:
            lineas_logicas.append((n_linea_buf, ''.join(linea_buf)))

        # ── Procesar cada línea lógica ────────────────────────────────────────
        for n_linea, linea in lineas_logicas:
            s = linea.strip()
            if not s:
                continue

            # #include ────────────────────────────────────────────────────────
            if RE_INCLUDE_LINE.match(s):
                if not self._activo():
                    continue
                nombre, funciones = self._parsear_include(linea)
                self._emit_import(nombre, lineas_salida, mapa_salida, fuente, n_linea)
                if funciones:
                    for func in funciones:
                        nombre_func = func.strip()
                        if not nombre_func:
                            continue
                        norm = nombre_func.lower()
                        if norm in self._externs_explicit:
                            continue
                        self._externs_explicit.add(norm)
                        lineas_salida.append(f".extern {nombre_func}")
                        mapa_salida.append(SourceLine(path=fuente, line=n_linea))

                if self._extern_placeholder_index is None:
                    self._extern_placeholder_index = len(lineas_salida)
                    lineas_salida.append(self._EXTERN_PLACEHOLDER)
                    mapa_salida.append(SourceLine(path=fuente, line=n_linea))
                continue

            # #define ─────────────────────────────────────────────────────────
            if RE_DEFINE_LINE.match(s):
                if self._activo():
                    macro = self._parsear_define(s)
                    self._defines[macro.nombre] = macro
                    self._define_pattern = None   # invalidar caché de patrón
                    self._log(f"Macro definida: {macro}")
                continue

            # #undef ──────────────────────────────────────────────────────────
            if RE_UNDEF_LINE.match(s):
                if self._activo():
                    nombre = self._parsear_nombre_macro(s, 'undef')
                    self._defines.pop(nombre, None)
                    self._define_pattern = None
                    self._log(f"Macro eliminada: {nombre}")
                continue

            # #ifdef ──────────────────────────────────────────────────────────
            if RE_IFDEF_LINE.match(s):
                nombre = self._parsear_nombre_macro(s, 'ifdef')
                activo = nombre in self._defines
                self._pila_cond.append(activo)
                self._log(f"#ifdef {nombre} → {'activo' if activo else 'ignorado'}")
                continue

            # #ifndef ─────────────────────────────────────────────────────────
            if RE_IFNDEF_LINE.match(s):
                nombre = self._parsear_nombre_macro(s, 'ifndef')
                activo = nombre not in self._defines
                self._pila_cond.append(activo)
                self._log(f"#ifndef {nombre} → {'activo' if activo else 'ignorado'}")
                continue

            # #else ───────────────────────────────────────────────────────────
            if RE_ELSE_LINE.match(s):
                if not self._pila_cond:
                    raise CondicionalError(
                        "#else sin #ifdef/#ifndef previo", fuente, n_linea
                    )
                self._pila_cond[-1] = not self._pila_cond[-1]
                continue

            # #endif ──────────────────────────────────────────────────────────
            if RE_ENDIF_LINE.match(s):
                if not self._pila_cond:
                    raise CondicionalError(
                        "#endif sin #ifdef/#ifndef previo", fuente, n_linea
                    )
                self._pila_cond.pop()
                continue

            # #error ──────────────────────────────────────────────────────────
            if RE_ERROR_LINE.match(s):
                if self._activo():
                    m = re.match(r'#\s*error\s*(.*)', s)
                    raise PreprocesadorError(
                        m.group(1).strip() if m else '', fuente, n_linea
                    )
                continue

            # #warning ────────────────────────────────────────────────────────
            if RE_WARNING_LINE.match(s):
                if self._activo():
                    m = re.match(r'#\s*warning\s*(.*)', s)
                    self._advertir(
                        m.group(1).strip() if m else '', fuente, n_linea
                    )
                continue

            # ── Línea de código (o comentario conservado) ────────────────────
            if not self._activo():
                continue

            linea_expandida = self._expandir_macros(linea)
            if linea_expandida.strip():
                lineas_salida.append(linea_expandida.rstrip())
                mapa_salida.append(SourceLine(path=fuente, line=n_linea))

        # Verificar bloques condicionales cerrados (solo en nivel raíz)
        if self._pila_cond:
            raise CondicionalError(
                f"Faltan {len(self._pila_cond)} directiva(s) #endif", fuente
            )

        return lineas_salida, mapa_salida

    def _finalizar_imports_externs(self, lineas: List[str],
                                   mapa: List[SourceLine]) -> None:
        if self._extern_placeholder_index is None:
            return

        auto_externs: set = set()
        if self._imports_set:
            definidos, referenciados = self._collect_symbol_sets(lineas)
            auto_externs = referenciados - definidos - self._externs_explicit

        idx = self._extern_placeholder_index
        if not auto_externs:
            del lineas[idx]
            del mapa[idx]
            return

        extern_lines = [f".extern {name}" for name in sorted(auto_externs)]
        ref = mapa[idx]
        lineas[idx:idx + 1] = extern_lines
        mapa[idx:idx + 1] = [ref for _ in extern_lines]

    def _reset_state(self) -> None:
        self._defines = dict(self._macros_base)
        self._define_pattern = None
        self._pila_cond = []
        self.advertencias = []
        self._imports_set = set()
        self._externs_explicit = set()
        self._extern_placeholder_index = None


    def preprocess(self, codigo: str,
                   nombre_fuente: str = '<string>') -> PreprocessResult:
        self._reset_state()

        lineas, mapa = self._procesar_tokens(codigo, nombre_fuente)

        self._finalizar_imports_externs(lineas, mapa)

        texto = '\n'.join(lineas)
        if texto:
            texto += '\n'

        return PreprocessResult(text=texto, line_map=mapa)

    def preprocess_archivo(self, ruta: str) -> PreprocessResult:
        ruta_abs = os.path.abspath(ruta)
        if not os.path.isfile(ruta_abs):
            raise IncludeError(f"Archivo no encontrado: '{ruta_abs}'")
        with open(ruta_abs, 'r', encoding='utf-8-sig') as f:
            contenido = f.read()
        return self.preprocess(contenido, nombre_fuente=ruta_abs)

    def listar_macros(self) -> Dict[str, str]:
        """Devuelve un dict con todas las macros actualmente activas."""
        return {k: repr(v) for k, v in self._defines.items()}



if __name__ == '__main__':
    def main():
        import argparse

        parser = argparse.ArgumentParser(
            description='Preprocesador CACAO_Core-64'
        )
        parser.add_argument('input', help='Archivo fuente a preprocesar')
        parser.add_argument(
            '-I', '--include-dir', dest='include_dir', default=None,
            help='Directorio base para #include'
        )
        args = parser.parse_args()

        try:
            pre = Preprocesador(library_dir=args.include_dir)
            result = pre.preprocess_archivo(args.input)
            sys.stdout.write(result.text)
        except PreprocesadorError as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(1)

    main()