
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import ply.lex as lex


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
  

    def __init__(self,
                 library_dir: Optional[str] = None,
                 max_include_depth: int = 25,
                 max_macro_expansion: int = 50,
                 macros_iniciales: Optional[Dict[str, str]] = None,
                 verbose: bool = False):

        self.library_dir          = self._resolver_library_dir(library_dir)
        self.max_include_depth    = max_include_depth
        self.max_macro_expansion  = max_macro_expansion
        self.verbose              = verbose
        self.advertencias: List[str] = []

        # Estado interno (se reinicia en cada llamada a preprocess)
        self._defines: Dict[str, Macro]    = {}
        self._define_pattern               = None
        self._include_stack: List[str]     = []  # cadena actual (ciclos)
        self._include_seen: set            = set()  # todos (evita dupes)
        self._pila_cond: List[bool]        = []  # bloques condicionales

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
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\(([^)]*)\)\s*(.*)', resto)
        if m:
            nombre = m.group(1)
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            valor  = m.group(3).strip()
            return Macro(nombre, valor, params)

        # Simple: NOMBRE  o  NOMBRE valor
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*(.*)', resto)
        if m:
            return Macro(m.group(1), m.group(2).strip() or '1')

        raise MacroError(f"Sintaxis #define inválida: {raw}")

    def _parsear_include(self, raw: str) -> Tuple[str, Optional[List[str]]]:
        """Extrae el nombre de archivo y lista de funciones de #include."""
        m = re.match(
            r'^\s*#\s*include\s+"([^"]+)"\s*(?:\{([^}]*)\})?\s*(?:(?://|;|#).*)?$',
            raw
        )
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

    def _filtrar_funciones(self, contenido: str, funciones: List[str],
                           fuente: str, n_linea: int) -> str:
        lineas = contenido.splitlines()
        salida = list(lineas)

        bloques = {}
        actual = None
        inicio = None
        marca_inicio = None

        for i, linea in enumerate(lineas):
            m = re.match(r'^\s*;\s*@func\s+([A-Za-z_][A-Za-z0-9_]*)\s*$', linea)
            if m:
                if actual is not None:
                    raise IncludeError("Bloque @func anidado o sin cerrar", fuente, n_linea)
                actual = m.group(1)
                if actual in bloques:
                    raise IncludeError(f"Funcion duplicada: {actual}", fuente, n_linea)
                inicio = i + 1
                marca_inicio = i
                continue

            if re.match(r'^\s*;\s*@endfunc\s*$', linea):
                if actual is None:
                    raise IncludeError("@endfunc sin @func", fuente, n_linea)
                bloques[actual] = (inicio, i, marca_inicio, i)
                actual = None
                inicio = None
                marca_inicio = None
                continue

        if actual is not None:
            raise IncludeError(f"Falta @endfunc para '{actual}'", fuente, n_linea)

        faltantes = [f for f in funciones if f not in bloques]
        if faltantes:
            raise IncludeError(
                "Funciones no encontradas: " + ", ".join(faltantes),
                fuente, n_linea
            )

        for nombre, (ini, fin, marca_ini, marca_fin) in bloques.items():
            salida[marca_ini] = ''
            salida[marca_fin] = ''
            if nombre not in funciones:
                for j in range(ini, fin):
                    salida[j] = ''

        texto = '\n'.join(salida)
        if contenido.endswith('\n'):
            texto += '\n'
        return texto

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


    def _resolver_include(self, nombre: str) -> str:
        """Devuelve la ruta absoluta del archivo a incluir."""
        ruta    = os.path.abspath(os.path.join(self.library_dir, nombre))
        lib_abs = os.path.abspath(self.library_dir)

        # Seguridad: no permitir salir de Libraries con ../
        if os.path.commonpath([ruta, lib_abs]) != lib_abs:
            raise IncludeError(
                f"#include intenta salir del directorio de bibliotecas: '{nombre}'"
            )
        if not os.path.isfile(ruta):
            raise IncludeError(f"Archivo no encontrado: '{ruta}'")
        return ruta

    def _procesar_include(self, nombre: str, fuente: str,
                          n_linea: int, depth: int,
                          funciones: Optional[List[str]] = None
                          ) -> Tuple[List[str], List[SourceLine]]:
        """Lee y preprocesa recursivamente un archivo incluido."""
        if depth > self.max_include_depth:
            raise IncludeError(
                "Profundidad máxima de #include superada. ¿Inclusión circular?",
                fuente, n_linea
            )

        ruta = self._resolver_include(nombre)

        # Detectar ciclo de inclusión
        if ruta in self._include_stack:
            ciclo = ' -> '.join(self._include_stack + [ruta])
            raise IncludeError(
                f"Inclusión circular detectada: {ciclo}", fuente, n_linea
            )

        # Evitar duplicados (include-guard automático)
        if ruta in self._include_seen:
            self._advertir(
                f"'{nombre}' ya fue incluido antes (se omite)", fuente, n_linea
            )
            return [], []

        self._include_seen.add(ruta)
        self._include_stack.append(ruta)
        self._log(f"#include '{nombre}' → {ruta}")

        try:
            with open(ruta, 'r', encoding='utf-8-sig') as f:
                contenido = f.read()
        except OSError as e:
            raise IncludeError(
                f"No se pudo leer '{ruta}': {e}", fuente, n_linea
            )

        if funciones:
            contenido = self._filtrar_funciones(contenido, funciones, fuente, n_linea)

        lineas, mapa = self._procesar_tokens(contenido, ruta, depth + 1)
        self._include_stack.pop()
        return lineas, mapa

    def _procesar_tokens(self, texto: str, fuente: str,
                         depth: int = 0) -> Tuple[List[str], List[SourceLine]]:
      
        lineas_salida: List[str]        = []
        mapa_salida:   List[SourceLine] = []

        # Clonar el lexer para soportar llamadas recursivas (#include)
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
            if re.match(r'#\s*include\b', s):
                if not self._activo():
                    continue
                nombre, funciones = self._parsear_include(linea)
                inc_l, inc_m = self._procesar_include(
                    nombre, fuente, n_linea, depth, funciones
                )
                lineas_salida.extend(inc_l)
                mapa_salida.extend(inc_m)
                continue

            # #define ─────────────────────────────────────────────────────────
            if re.match(r'#\s*define\b', s):
                if self._activo():
                    macro = self._parsear_define(s)
                    self._defines[macro.nombre] = macro
                    self._define_pattern = None   # invalidar caché de patrón
                    self._log(f"Macro definida: {macro}")
                continue

            # #undef ──────────────────────────────────────────────────────────
            if re.match(r'#\s*undef\b', s):
                if self._activo():
                    nombre = self._parsear_nombre_macro(s, 'undef')
                    self._defines.pop(nombre, None)
                    self._define_pattern = None
                    self._log(f"Macro eliminada: {nombre}")
                continue

            # #ifdef ──────────────────────────────────────────────────────────
            if re.match(r'#\s*ifdef\b', s):
                nombre = self._parsear_nombre_macro(s, 'ifdef')
                activo = nombre in self._defines
                self._pila_cond.append(activo)
                self._log(f"#ifdef {nombre} → {'activo' if activo else 'ignorado'}")
                continue

            # #ifndef ─────────────────────────────────────────────────────────
            if re.match(r'#\s*ifndef\b', s):
                nombre = self._parsear_nombre_macro(s, 'ifndef')
                activo = nombre not in self._defines
                self._pila_cond.append(activo)
                self._log(f"#ifndef {nombre} → {'activo' if activo else 'ignorado'}")
                continue

            # #else ───────────────────────────────────────────────────────────
            if re.match(r'#\s*else\b', s):
                if not self._pila_cond:
                    raise CondicionalError(
                        "#else sin #ifdef/#ifndef previo", fuente, n_linea
                    )
                self._pila_cond[-1] = not self._pila_cond[-1]
                continue

            # #endif ──────────────────────────────────────────────────────────
            if re.match(r'#\s*endif\b', s):
                if not self._pila_cond:
                    raise CondicionalError(
                        "#endif sin #ifdef/#ifndef previo", fuente, n_linea
                    )
                self._pila_cond.pop()
                continue

            # #error ──────────────────────────────────────────────────────────
            if re.match(r'#\s*error\b', s):
                if self._activo():
                    m = re.match(r'#\s*error\s*(.*)', s)
                    raise PreprocesadorError(
                        m.group(1).strip() if m else '', fuente, n_linea
                    )
                continue

            # #warning ────────────────────────────────────────────────────────
            if re.match(r'#\s*warning\b', s):
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
        if depth == 0 and self._pila_cond:
            raise CondicionalError(
                f"Faltan {len(self._pila_cond)} directiva(s) #endif", fuente
            )

        return lineas_salida, mapa_salida



    def preprocess(self, codigo: str,
                   nombre_fuente: str = '<string>') -> PreprocessResult:
        # Reiniciar todo el estado interno
        self._defines        = dict(self._macros_base)
        self._define_pattern = None
        self._include_stack  = []
        self._include_seen   = set()
        self._pila_cond      = []
        self.advertencias    = []

        lineas, mapa = self._procesar_tokens(codigo, nombre_fuente, depth=0)

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