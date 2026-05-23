import os
import sys
from typing import Dict, List, Optional, Tuple, Set

from .errors import CondicionalError, IncludeError, MacroError, PreprocesadorError
from .lexer_high_level import build_lexer
from .models import Macro, PreprocessResult, SourceLine


class Preprocesador:
    def __init__(
        self,
        max_macro_expansion: int = 50,
        macros_iniciales: Optional[Dict[str, str]] = None,
        verbose: bool = False,
        fs=None,  # Optional filesystem provider (SimpleFS)
    ):
        # Inicializa el preprocesador con estado vacío y configuración
        self.max_macro_expansion = max_macro_expansion
        self.verbose = verbose
        self.advertencias: List[str] = []

        # Optional filesystem provider used to resolve #include from disk
        self.fs = fs

        self._defines: Dict[str, Macro] = {}
        self._pila_cond: List[bool] = []
        self._imports_set: set = set()
        self._externs_explicit: set = set()
        self._librerias_importadas: Dict[str, str] = {}  # calificador (e.g. "math.lib") -> nombre_archivo
        self._funciones_por_libreria: Dict[str, List[Tuple[str, SourceLine]]] = {}

        # Seguimiento de imports desde codigo fuente
        self._include_stack: List[str] = []
        self._included_sources: Set[str] = set()
        self._source_defs: Dict[str, Set[str]] = {}
        self._source_exports_decl: Dict[str, Set[str]] = {}
        self._source_exports: Dict[str, Set[str]] = {}
        self._source_internals: Dict[str, Set[str]] = {}
        self._source_imports: Dict[str, Set[str]] = {}
        self._public_symbols: Dict[str, str] = {}
        self._export_decl_lines: Dict[str, Dict[str, int]] = {}

        self._macros_base: Dict[str, Macro] = {}
        if macros_iniciales:
            self._macros_base.update({
                k: Macro(k, str(v)) for k, v in macros_iniciales.items()
            })

        self._lexer = build_lexer()

    # ======================== UTILIDADES CORE ========================
    
    def _activo(self) -> bool:
        """Verifica si el código actual está activo según condicionales."""
        return all(self._pila_cond) if self._pila_cond else True

    # ======================== PARSING LÉXICO ========================

    def _leer_identificador(self, texto: str, indice: int) -> Tuple[str, int]:
        """Lee un identificador desde el índice."""
        if indice >= len(texto) or not (texto[indice].isalpha() or texto[indice] == "_"):
            return "", indice
        inicio = indice
        indice += 1
        while indice < len(texto) and (texto[indice].isalnum() or texto[indice] == "_"):
            indice += 1
        return texto[inicio:indice], indice

    def _es_inicio_identificador(self, caracter: str) -> bool:
        """Verifica si un carácter puede iniciar un identificador."""
        return caracter.isalpha() or caracter == "_"

    def _es_identificador(self, caracter: str) -> bool:
        """Verifica si un carácter es válido dentro de un identificador."""
        return caracter.isalnum() or caracter == "_"

    def _saltar_espacios(self, texto: str, indice: int) -> int:
        """Salta espacios en blanco desde el índice dado."""
        while indice < len(texto) and texto[indice].isspace():
            indice += 1
        return indice

    # ======================== PARSING DE DIRECTIVAS ========================

    def _extraer_payload_directiva(self, linea_raw: str, nombre_directiva: str) -> str:
        """Extrae contenido de una directiva después del nombre."""
        linea = self._strip_comment(linea_raw).lstrip()
        if not linea.startswith(f"#{nombre_directiva}"):
            raise PreprocesadorError(f"Sintaxis inválida: {linea_raw}")
        return linea[1+len(nombre_directiva):].lstrip()

    def _obtener_nombre_directiva(self, linea_raw: str) -> Optional[str]:
        """Extrae nombre de directiva o None."""
        linea = self._strip_comment(linea_raw).lstrip()
        if not linea.startswith("#"):
            return None
        idx = 1
        while idx < len(linea) and linea[idx].isspace(): idx += 1
        nombre, _ = self._leer_identificador(linea, idx)
        return nombre

    def _leer_argumentos_parentesis(self, texto: str, idx: int) -> Tuple[Optional[List[str]], int]:
        """Lee argumentos entre paréntesis, maneja nidos."""
        if idx >= len(texto) or texto[idx] != "(": 
            return None, idx
        prof, args, buf = 0, [], []
        while idx < len(texto):
            c = texto[idx]
            if c == "(": 
                prof += 1
                if prof > 1: buf.append(c)
            elif c == ")":
                prof -= 1
                args.append("".join(buf).strip())
                if prof == 0: 
                    return [a for a in args if a], idx + 1
                buf.append(c)
            elif c == "," and prof == 1:
                args.append("".join(buf).strip())
                buf = []
            else:
                buf.append(c)
            idx += 1
        return None, idx

    def _parsear_define(self, linea_raw: str) -> Macro:
        """Parsea #define y retorna Macro."""
        cuerpo = self._extraer_payload_directiva(linea_raw, "define")
        idx = 0
        while idx < len(cuerpo) and cuerpo[idx].isspace(): idx += 1
        nombre, idx = self._leer_identificador(cuerpo, idx)
        if not nombre: raise MacroError(f"#define inválido: {linea_raw}")
        while idx < len(cuerpo) and cuerpo[idx].isspace(): idx += 1
        params = None
        if idx < len(cuerpo) and cuerpo[idx] == "(":
            params, idx = self._leer_argumentos_parentesis(cuerpo, idx)
            if params is None: raise MacroError(f"#define inválido: {linea_raw}")
        valor = (cuerpo[idx:].strip() if idx < len(cuerpo) else "") or "1"
        return Macro(nombre, valor, params)

    def _parsear_include(self, linea_raw: str) -> Tuple[str, Optional[List[str]]]:
        """Parsea #include y retorna (archivo, funciones_o_none)."""
        payload = self._extraer_payload_directiva(linea_raw, "include")
        idx = 0
        while idx < len(payload) and payload[idx].isspace(): idx += 1
        if idx >= len(payload) or payload[idx] != '"': 
            raise IncludeError(f"#include inválido: {linea_raw}")
        idx += 1
        fin = payload.find('"', idx)
        if fin == -1: raise IncludeError(f"#include inválido: {linea_raw}")
        nombre = payload[idx:fin]
        resto = payload[fin+1:].strip()
        if not resto: return nombre, None
        if not resto.startswith("{"): raise IncludeError(f"#include inválido: {linea_raw}")
        fin_llave = resto.find("}")
        if fin_llave == -1: raise IncludeError(f"#include inválido: {linea_raw}")
        lista = resto[1:fin_llave].strip()
        if resto[fin_llave+1:].strip(): raise IncludeError(f"#include inválido: {linea_raw}")
        funcs = self._parsear_lista_nombres(lista)
        return nombre, funcs if funcs else None

    def _parsear_lista_nombres(
        self,
        lista_raw: str,
        fuente: Optional[str] = None,
        numero_linea: Optional[int] = None,
    ) -> List[str]:
        """Parsea lista separada por comas y valida que tenga elementos."""
        nombres = [f.strip() for f in lista_raw.split(",") if f.strip()]
        if not nombres:
            raise PreprocesadorError("Lista vacia en directiva", fuente, numero_linea)
        return nombres

    def _parsear_export(self, linea_raw: str, fuente: str, numero_linea: int) -> List[str]:
        """Parsea #export y retorna lista de nombres."""
        payload = self._extraer_payload_directiva(linea_raw, "export")
        if not payload:
            raise PreprocesadorError(f"#export inválido: {linea_raw}", fuente, numero_linea)
        payload = payload.strip()
        if payload.startswith("{"):
            fin_llave = payload.find("}")
            if fin_llave == -1:
                raise PreprocesadorError(f"#export inválido: {linea_raw}", fuente, numero_linea)
            lista = payload[1:fin_llave].strip()
            if payload[fin_llave+1:].strip():
                raise PreprocesadorError(f"#export inválido: {linea_raw}", fuente, numero_linea)
            return self._parsear_lista_nombres(lista, fuente, numero_linea)
        return self._parsear_lista_nombres(payload, fuente, numero_linea)

    def _parsear_nombre_macro(self, linea_raw: str, dir_name: str) -> str:
        """Extrae nombre de macro de directivas."""
        payload = self._extraer_payload_directiva(linea_raw, dir_name)
        idx = 0
        while idx < len(payload) and payload[idx].isspace(): idx += 1
        nombre, _ = self._leer_identificador(payload, idx)
        if not nombre: raise PreprocesadorError(f"#{dir_name} inválido: {linea_raw}")
        return nombre

    # ======================== IMPORTS DESDE FUENTE ========================

    def _es_import_compilado(self, nombre: str) -> bool:
        lower = nombre.lower()
        return lower.endswith(".lib") or lower.endswith(".reloc") or lower.endswith(".obj")

    def _resolver_ruta_include(self, nombre: str, fuente: str) -> str:
        """Resuelve ruta de include. Si se proporcionó un proveedor de FS, resuelve
        exclusivamente en el disco simulado y devuelve una ruta normalizada que
        comienza con '/' (ej. '/libs/math.lib'). Si no hay FS, mantiene el
        comportamiento original basado en el host.
        """
        if self.fs:
            # Buscar como ruta absoluta en FS
            if nombre.startswith('/'):
                key = nombre.lstrip('/')
                try:
                    self.fs.read_file(key)
                    return '/' + key
                except Exception:
                    pass

            # Si la fuente es un archivo del disco (ruta que comienza con '/'),
            # resolver ruta relativa dentro del disco
            if fuente and fuente.startswith('/'):
                base = os.path.dirname(fuente.lstrip('/'))
                candidate = (base + '/' + nombre).lstrip('/') if base else nombre.lstrip('/')
                try:
                    self.fs.read_file(candidate)
                    return '/' + candidate
                except Exception:
                    pass

            # Buscar en ubicaciones comunes dentro del disco
            common_prefixes = ["system", "libs", "examples", "src/examples"]
            for prefix in common_prefixes:
                candidate = f"{prefix}/{nombre}".lstrip('/')
                try:
                    self.fs.read_file(candidate)
                    return '/' + candidate
                except Exception:
                    pass

            raise IncludeError(f"Archivo no encontrado en disco: '{nombre}'", fuente, None)

        # Fallback: comportamiento anterior (host filesystem)
        if os.path.isabs(nombre):
            return os.path.abspath(nombre)
        if fuente and os.path.isfile(fuente):
            base_dir = os.path.dirname(fuente)
        else:
            base_dir = os.getcwd()
        candidato = os.path.abspath(os.path.join(base_dir, nombre))
        if os.path.isfile(candidato):
            return candidato

        encontrado = self._buscar_en_examples(nombre, base_dir)
        if encontrado:
            return encontrado

        return candidato

    def _buscar_en_examples(self, nombre: str, base_dir: str) -> Optional[str]:
        """Busca un include dentro de src/examples (incluye subdirectorios)."""
        candidatos = []
        for root in (base_dir, os.getcwd()):
            src_examples = os.path.join(root, "src", "examples")
            if os.path.isdir(src_examples):
                candidatos.append(src_examples)
            examples = os.path.join(root, "examples")
            if os.path.isdir(examples):
                candidatos.append(examples)

        for directorio in candidatos:
            direct_path = os.path.join(directorio, nombre)
            if os.path.isfile(direct_path):
                return os.path.abspath(direct_path)

        for directorio in candidatos:
            for dirpath, _, filenames in os.walk(directorio):
                if nombre in filenames:
                    return os.path.abspath(os.path.join(dirpath, nombre))

        return None

    def _registrar_export(self, fuente: str, nombres: List[str], numero_linea: int) -> None:
        decl = self._source_exports_decl.setdefault(fuente, set())
        lineas = self._export_decl_lines.setdefault(fuente, {})
        for nombre in nombres:
            if nombre in decl:
                continue
            decl.add(nombre)
            lineas[nombre] = numero_linea

    def _registrar_definicion(self, fuente: str, nombre: str) -> None:
        defs = self._source_defs.setdefault(fuente, set())
        defs.add(nombre)

    def _finalizar_archivo(self, fuente: str) -> None:
        if fuente in self._source_exports:
            return
        defs = self._source_defs.get(fuente, set())
        exports_decl = self._source_exports_decl.get(fuente, set())
        if exports_decl:
            missing = exports_decl - defs
            if missing:
                nombre = sorted(missing)[0]
                linea = self._export_decl_lines.get(fuente, {}).get(nombre, 0)
                raise IncludeError(
                    f"Export no definido en '{fuente}': {sorted(missing)}",
                    fuente,
                    linea,
                )
            exports = set(exports_decl)
        else:
            exports = set(defs)
        self._source_exports[fuente] = exports
        self._source_internals[fuente] = set(defs) - exports

    def _registrar_publicos(
        self,
        fuente_origen: str,
        ruta_modulo: str,
        nombres: Set[str],
        numero_linea: int,
    ) -> None:
        for nombre in nombres:
            if nombre in self._public_symbols and self._public_symbols[nombre] != ruta_modulo:
                raise IncludeError(
                    f"Conflicto de simbolo '{nombre}' entre '{ruta_modulo}' y '{self._public_symbols[nombre]}'",
                    fuente_origen,
                    numero_linea,
                )
            self._public_symbols[nombre] = ruta_modulo

    def _registrar_imports(
        self,
        ruta_modulo: str,
        funciones: Optional[List[str]],
        fuente_origen: str,
        numero_linea: int,
    ) -> None:
        self._finalizar_archivo(ruta_modulo)
        exports = self._source_exports.get(ruta_modulo, set())
        if funciones:
            solicitadas = set(funciones)
            missing = solicitadas - exports
            if missing:
                raise IncludeError(
                    f"Simbolo(s) no exportado(s) en '{ruta_modulo}': {sorted(missing)}",
                    fuente_origen,
                    numero_linea,
                )
        else:
            solicitadas = set(exports)

        self._source_imports.setdefault(ruta_modulo, set()).update(solicitadas)
        self._registrar_publicos(fuente_origen, ruta_modulo, solicitadas, numero_linea)

    def _detectar_definicion(self, linea: str) -> Optional[str]:
        codigo = self._strip_comment(linea).lstrip()
        if not codigo:
            return None
        for keyword in ("func", "let"):
            if codigo.startswith(keyword):
                idx = len(keyword)
                if idx < len(codigo) and not codigo[idx].isspace():
                    continue
                idx = self._saltar_espacios(codigo, idx)
                nombre, _ = self._leer_identificador(codigo, idx)
                return nombre or None
        return None

    def _delta_nivel_bloque(self, linea: str) -> int:
        codigo = self._strip_comment(linea)
        en_simple = False
        en_doble = False
        delta = 0
        for ch in codigo:
            if ch == "'" and not en_doble:
                en_simple = not en_simple
                continue
            if ch == '"' and not en_simple:
                en_doble = not en_doble
                continue
            if en_simple or en_doble:
                continue
            if ch == "{":
                delta += 1
            elif ch == "}":
                delta -= 1
        return delta

    # ======================== MANEJO DE COMENTARIOS ========================

    def _strip_comment(self, line: str) -> str:
        """Elimina comentarios // respetando strings."""
        en_simple, en_doble, idx = False, False, 0
        while idx < len(line):
            if line[idx] == "'" and not en_doble: en_simple = not en_simple
            elif line[idx] == '"' and not en_simple: en_doble = not en_doble
            elif not en_simple and not en_doble and idx + 1 < len(line) and line[idx:idx+2] == "//":
                return line[:idx]
            idx += 1
        return line

    def _find_comment_start(self, line: str) -> Optional[int]:
        """Encuentra el índice donde inicia un comentario // respetando strings."""
        en_simple, en_doble, idx = False, False, 0
        while idx < len(line):
            if line[idx] == "'" and not en_doble: en_simple = not en_simple
            elif line[idx] == '"' and not en_simple: en_doble = not en_doble
            elif not en_simple and not en_doble and idx + 1 < len(line) and line[idx:idx+2] == "//":
                return idx
            idx += 1
        return None

    # ======================== EMISIÓN DE DIRECTIVAS ========================

    def _emit_import(
        self,
        nombre_lib: str,
        lineas_salida: List[str],
        mapa_salida: List[SourceLine],
        fuente: str,
        numero_linea: int,
    ) -> None:
        """Emite una directiva .import evitando duplicados.
        Se ejecuta cuando se procesa #include."""
        if nombre_lib in self._imports_set:
            return
        self._imports_set.add(nombre_lib)
        lineas_salida.append(f'.import "{nombre_lib}"')
        mapa_salida.append(SourceLine(path=fuente, line=numero_linea))



    # ======================== DETECCIÓN Y REEMPLAZO DE FUNCIONES CALIFICADAS ========================

    def _extractar_funciones_calificadas(self, codigo: str) -> Dict[str, str]:
        """Detecta llamadas a funciones calificadas como math.lib.sqrt().
        Retorna diccionario: {"math.lib.sqrt" -> "sqrt"} para reemplazo posterior.
        This is parte de la auto-detección de imports: si ves math.lib.sqrt(),
        automáticamente registra que sqrt pertenece a math.lib."""
        funciones_encontradas: Dict[str, str] = {}
        indice = 0

        while indice < len(codigo):
            if self._es_inicio_identificador(codigo[indice]):
                inicio = indice
                # Leer primer identificador (e.g., "math")
                nombre1, siguiente_indice = self._leer_identificador(codigo, indice)
                
                # Verificar si hay un punto
                siguiente_indice = self._saltar_espacios(codigo, siguiente_indice)
                if siguiente_indice < len(codigo) and codigo[siguiente_indice] == ".":
                    # Intentar leer segundo identificador (e.g., "lib")
                    siguiente_indice = self._saltar_espacios(codigo, siguiente_indice + 1)
                    nombre2, siguiente_indice = self._leer_identificador(codigo, siguiente_indice)
                    
                    if nombre2:
                        calificador = f"{nombre1}.{nombre2}"
                        # Verificar si hay otro punto (para la función)
                        siguiente_indice = self._saltar_espacios(codigo, siguiente_indice)
                        if siguiente_indice < len(codigo) and codigo[siguiente_indice] == ".":
                            siguiente_indice = self._saltar_espacios(codigo, siguiente_indice + 1)
                            nombre_funcion, siguiente_indice = self._leer_identificador(codigo, siguiente_indice)
                            
                            if nombre_funcion and calificador in self._librerias_importadas:
                                # Es una llamada calificada de una librería importada
                                clave = f"{calificador}.{nombre_funcion}"
                                funciones_encontradas[clave] = nombre_funcion
                                indice = siguiente_indice
                                continue
                
                indice = siguiente_indice
            else:
                indice += 1

        return funciones_encontradas

    def _reemplazar_funciones_calificadas(self, codigo: str) -> str:
        """Reemplaza llamadas calificadas por simples: math.lib.sqrt(x) -> sqrt(x).
        El compilador podrá resolver sqrt usando el .extern.
        Esto limpia la sintaxis antes de enviar al compilador."""
        resultado: List[str] = []
        indice = 0

        while indice < len(codigo):
            if self._es_inicio_identificador(codigo[indice]):
                inicio = indice
                nombre1, siguiente_indice = self._leer_identificador(codigo, indice)
                
                siguiente_indice_temp = self._saltar_espacios(codigo, siguiente_indice)
                if siguiente_indice_temp < len(codigo) and codigo[siguiente_indice_temp] == ".":
                    nombre2, siguiente_indice2 = self._leer_identificador(
                        codigo, self._saltar_espacios(codigo, siguiente_indice_temp + 1)
                    )
                    
                    if nombre2:
                        calificador = f"{nombre1}.{nombre2}"
                        siguiente_indice2_temp = self._saltar_espacios(codigo, siguiente_indice2)
                        if siguiente_indice2_temp < len(codigo) and codigo[siguiente_indice2_temp] == ".":
                            nombre_funcion, siguiente_indice3 = self._leer_identificador(
                                codigo, self._saltar_espacios(codigo, siguiente_indice2_temp + 1)
                            )
                            
                            if nombre_funcion and calificador in self._librerias_importadas:
                                # Reemplazar calificador.funcion por solo funcion
                                resultado.append(nombre_funcion)
                                indice = siguiente_indice3
                                continue
                
                resultado.append(nombre1)
                indice = siguiente_indice
            else:
                resultado.append(codigo[indice])
                indice += 1

        return "".join(resultado)

    # ======================== EXPANSIÓN Y REEMPLAZO DE MACROS ========================

    def _reemplazar_macro_parametrizada(self, codigo: str, macro_def: Macro) -> str:
        """Reemplaza una macro con parámetros en el código.
        Encuentra SQUARE(5) y reemplaza por ((5) * (5)).
        Se aplica recursivamente hasta convergencia (con límite max_macro_expansion)."""
        nombre_macro = macro_def.nombre
        resultado: List[str] = []
        indice = 0

        while indice < len(codigo):
            if codigo.startswith(nombre_macro, indice):
                indice_fin = indice + len(nombre_macro)
                if indice > 0 and self._es_identificador(codigo[indice - 1]):
                    resultado.append(codigo[indice])
                    indice += 1
                    continue
                if indice_fin < len(codigo) and codigo[indice_fin] == "(":
                    argumentos, siguiente_indice = self._leer_argumentos_parentesis(
                        codigo, indice_fin
                    )
                    if argumentos is not None:
                        resultado.append(macro_def.expandir(argumentos))
                        indice = siguiente_indice
                        continue

            resultado.append(codigo[indice])
            indice += 1

        return "".join(resultado)

    def _reemplazar_macros_simples(self, codigo: str) -> str:
        """Reemplaza macros sin parámetros en el código.
        Encuentra PI en código y reemplaza por 3.14159.
        Usa parsing manual para no reemplazar dentro de identificadores."""
        resultado: List[str] = []
        indice = 0

        while indice < len(codigo):
            caracter = codigo[indice]
            if self._es_inicio_identificador(caracter):
                nombre, siguiente_indice = self._leer_identificador(codigo, indice)
                macro_def = self._defines.get(nombre)
                if macro_def and macro_def.parametros is None and macro_def.valor:
                    resultado.append(macro_def.valor)
                else:
                    resultado.append(nombre)
                indice = siguiente_indice
                continue

            resultado.append(caracter)
            indice += 1

        return "".join(resultado)

    def _expandir_macros(self, linea: str) -> str:
        """Ejecuta la expansión completa de macros en una línea.
        1. Separa comentarios (no expandir dentro de comentarios)
        2. Expande macros parametrizadas (primer pasada)
        3. Itera reemplazando macros simples hasta convergencia
        4. Reintegra comentarios"""
        indice_comentario = self._find_comment_start(linea)
        codigo = linea[:indice_comentario] if indice_comentario is not None else linea
        comentario = linea[indice_comentario:] if indice_comentario is not None else ""

        # Primero: macros parametrizadas
        for macro_def in self._defines.values():
            if macro_def.parametros is not None:
                codigo = self._reemplazar_macro_parametrizada(codigo, macro_def)

        # Segundo: macros simples (iterativo hasta convergencia)
        for _ in range(self.max_macro_expansion):
            codigo_anterior = codigo
            codigo = self._reemplazar_macros_simples(codigo)
            if codigo == codigo_anterior:
                break
        else:
            raise MacroError("Limite de expansion de macros alcanzado")

        return codigo + comentario

    def _procesar_archivo_fuente(
        self,
        ruta: str,
        funciones: Optional[List[str]],
        fuente_origen: str,
        numero_linea: int,
    ) -> Tuple[List[str], List[SourceLine]]:
        """Procesa un archivo fuente incluido, con deteccion de ciclos.

        Si se proporcionó self.fs, lee el contenido desde el disco simulado en lugar
        del filesystem del host. Las rutas devueltas por _resolver_ruta_include
        se normalizan para comenzar con '/'.
        """
        # Normalizar ruta absoluta en el contexto del FS o host
        if self.fs and ruta.startswith('/'):
            ruta_absoluta = ruta
        elif self.fs and not ruta.startswith('/'):
            ruta_absoluta = '/' + ruta.lstrip('/')
        else:
            ruta_absoluta = os.path.abspath(ruta)

        if ruta_absoluta in self._include_stack:
            ruta_ciclo = " -> ".join(self._include_stack + [ruta_absoluta])
            raise IncludeError(f"Import circular detectado: {ruta_ciclo}", fuente_origen, numero_linea)

        if ruta_absoluta in self._included_sources:
            self._registrar_imports(ruta_absoluta, funciones, fuente_origen, numero_linea)
            return [], []

        # Leer desde disco simulado si está disponible
        self._include_stack.append(ruta_absoluta)
        prev_pila = self._pila_cond
        self._pila_cond = []
        try:
            if self.fs:
                key = ruta_absoluta.lstrip('/')
                try:
                    raw = self.fs.read_file(key)
                except Exception:
                    raise IncludeError(f"Archivo no encontrado: '{ruta_absoluta}'", fuente_origen, numero_linea)
                try:
                    contenido = raw.decode('utf-8-sig')
                except Exception:
                    contenido = raw.decode('utf-8', errors='replace')
                lineas_salida, mapa_salida = self._procesar_texto(contenido, ruta_absoluta)
            else:
                if not os.path.isfile(ruta_absoluta):
                    raise IncludeError(f"Archivo no encontrado: '{ruta_absoluta}'", fuente_origen, numero_linea)
                with open(ruta_absoluta, "r", encoding="utf-8-sig") as f:
                    contenido = f.read()
                lineas_salida, mapa_salida = self._procesar_texto(contenido, ruta_absoluta)
        finally:
            self._pila_cond = prev_pila
            self._include_stack.pop()

        self._included_sources.add(ruta_absoluta)
        self._registrar_imports(ruta_absoluta, funciones, fuente_origen, numero_linea)
        return lineas_salida, mapa_salida

    def _procesar_texto(
        self, texto: str, fuente: str
    ) -> Tuple[List[str], List[SourceLine]]:
        """Primera pasada: procesa directivas y codigo, con soporte de includes."""
        lineas_salida: List[str] = []
        mapa_salida: List[SourceLine] = []

        lexer = self._lexer.clone()
        lexer.lineno = 1
        lexer.input(texto)

        buffer_linea: List[str] = []
        numero_linea_buffer = 1
        lineas_logicas: List[Tuple[int, str]] = []

        for token in lexer:
            if token.type == "NEWLINE":
                lineas_logicas.append((numero_linea_buffer, "".join(buffer_linea)))
                buffer_linea = []
                numero_linea_buffer = lexer.lineno
            else:
                buffer_linea.append(token.value)

        if buffer_linea:
            lineas_logicas.append((numero_linea_buffer, "".join(buffer_linea)))

        nivel_bloque = 0

        for numero_linea, linea_original in lineas_logicas:
            linea_recortada = linea_original.strip()
            if not linea_recortada:
                continue

            nombre_directiva = self._obtener_nombre_directiva(linea_original)
            if nombre_directiva is not None:
                if not nombre_directiva:
                    raise PreprocesadorError(
                        "Directiva sin nombre", fuente, numero_linea
                    )

                if nombre_directiva == "include":
                    if not self._activo():
                        continue
                    nombre_archivo, funciones = self._parsear_include(linea_original)
                    if self._es_import_compilado(nombre_archivo):
                        self._emit_import(
                            nombre_archivo,
                            lineas_salida,
                            mapa_salida,
                            fuente,
                            numero_linea,
                        )
                        # Registrar libreria para deteccion de llamadas calificadas
                        self._librerias_importadas[nombre_archivo] = nombre_archivo

                        if funciones:
                            for funcion in funciones:
                                nombre_funcion = funcion.strip()
                                if not nombre_funcion:
                                    continue
                                nombre_normalizado = nombre_funcion.lower()
                                if nombre_normalizado in self._externs_explicit:
                                    continue
                                self._externs_explicit.add(nombre_normalizado)
                                lineas_salida.append(f".extern {nombre_funcion}")
                                mapa_salida.append(
                                    SourceLine(path=fuente, line=numero_linea)
                                )
                        continue

                    ruta_include = self._resolver_ruta_include(nombre_archivo, fuente)
                    lineas_inc, mapa_inc = self._procesar_archivo_fuente(
                        ruta_include,
                        funciones,
                        fuente,
                        numero_linea,
                    )
                    lineas_salida.extend(lineas_inc)
                    mapa_salida.extend(mapa_inc)
                    continue

                if nombre_directiva == "export":
                    if self._activo():
                        nombres = self._parsear_export(linea_original, fuente, numero_linea)
                        self._registrar_export(fuente, nombres, numero_linea)
                    continue

                if nombre_directiva == "define":
                    if self._activo():
                        macro = self._parsear_define(linea_original)
                        self._defines[macro.nombre] = macro
                    continue

                if nombre_directiva == "undef":
                    if self._activo():
                        nombre_macro = self._parsear_nombre_macro(linea_original, "undef")
                        self._defines.pop(nombre_macro, None)
                    continue

                if nombre_directiva == "ifdef":
                    nombre_macro = self._parsear_nombre_macro(linea_original, "ifdef")
                    self._pila_cond.append(nombre_macro in self._defines)
                    continue

                if nombre_directiva == "ifndef":
                    nombre_macro = self._parsear_nombre_macro(linea_original, "ifndef")
                    self._pila_cond.append(nombre_macro not in self._defines)
                    continue

                if nombre_directiva == "else":
                    if not self._pila_cond:
                        raise CondicionalError(
                            "#else sin #ifdef/#ifndef previo", fuente, numero_linea
                        )
                    self._pila_cond[-1] = not self._pila_cond[-1]
                    continue

                if nombre_directiva == "endif":
                    if not self._pila_cond:
                        raise CondicionalError(
                            "#endif sin #ifdef/#ifndef previo", fuente, numero_linea
                        )
                    self._pila_cond.pop()
                    continue

                if nombre_directiva == "error":
                    if self._activo():
                        mensaje = self._extraer_payload_directiva(
                            linea_original, "error"
                        )
                        raise PreprocesadorError(mensaje, fuente, numero_linea)
                    continue

                if nombre_directiva == "warning":
                    if self._activo():
                        mensaje = self._extraer_payload_directiva(linea_original, "warning")
                        self.advertencias.append(f"[{fuente}:{numero_linea}] {mensaje}")
                    continue

                raise PreprocesadorError(
                    f"Directiva desconocida: #{nombre_directiva}",
                    fuente,
                    numero_linea,
                )

            if not self._activo():
                continue

            # Es linea de codigo
            linea_expandida = self._expandir_macros(linea_original)

            if nivel_bloque == 0:
                definicion = self._detectar_definicion(linea_expandida)
                if definicion:
                    self._registrar_definicion(fuente, definicion)

            # Detectar funciones calificadas (para procesar despues)
            funciones_calificadas = self._extractar_funciones_calificadas(linea_expandida)
            for clave_calificada, nombre_funcion in funciones_calificadas.items():
                partes = clave_calificada.rsplit(".", 1)
                if len(partes) == 2:
                    nombre_libreria = partes[0]
                    nombre_normalizado = nombre_funcion.lower()
                    if nombre_normalizado not in self._externs_explicit:
                        if nombre_libreria not in self._funciones_por_libreria:
                            self._funciones_por_libreria[nombre_libreria] = []
                        self._funciones_por_libreria[nombre_libreria].append(
                            (nombre_funcion, SourceLine(path=fuente, line=numero_linea))
                        )

            # Reemplazar llamadas calificadas por llamadas simples
            linea_reemplazada = self._reemplazar_funciones_calificadas(linea_expandida)

            if linea_reemplazada.strip():
                lineas_salida.append(linea_reemplazada.rstrip())
                mapa_salida.append(SourceLine(path=fuente, line=numero_linea))

            nivel_bloque += self._delta_nivel_bloque(linea_reemplazada)
            if nivel_bloque < 0:
                nivel_bloque = 0

        if self._pila_cond:
            raise CondicionalError(
                f"Faltan {len(self._pila_cond)} directiva(s) #endif", fuente
            )

        self._finalizar_archivo(fuente)
        return lineas_salida, mapa_salida

    def _organizar_externs(
        self,
        lineas_salida: List[str],
        mapa_salida: List[SourceLine],
    ) -> Tuple[List[str], List[SourceLine]]:
        """Segunda pasada: inserta .extern debajo de su .import."""
        lineas_salida_organizada: List[str] = []
        mapa_salida_organizada: List[SourceLine] = []

        i = 0
        while i < len(lineas_salida):
            linea_actual = lineas_salida[i]
            lineas_salida_organizada.append(linea_actual)
            mapa_salida_organizada.append(mapa_salida[i])

            if linea_actual.startswith('.import "'):
                nombre_lib_with_quotes = linea_actual[9:]
                nombre_lib = nombre_lib_with_quotes.rstrip('"')

                if nombre_lib in self._funciones_por_libreria:
                    funciones_vistas = set()
                    for nombre_funcion, source_line in sorted(
                        self._funciones_por_libreria[nombre_lib],
                        key=lambda x: x[0],
                    ):
                        nombre_normalizado = nombre_funcion.lower()
                        if (
                            nombre_normalizado not in self._externs_explicit
                            and nombre_normalizado not in funciones_vistas
                        ):
                            lineas_salida_organizada.append(f".extern {nombre_funcion}")
                            mapa_salida_organizada.append(source_line)
                            self._externs_explicit.add(nombre_normalizado)
                            funciones_vistas.add(nombre_normalizado)

            i += 1

        return lineas_salida_organizada, mapa_salida_organizada

    def _reset_state(self) -> None:
        """Reinicia estado para procesar próximo archivo."""
        self._defines = dict(self._macros_base)
        self._pila_cond = []
        self.advertencias = []
        self._imports_set = set()
        self._externs_explicit = set()
        self._librerias_importadas = {}
        self._funciones_por_libreria = {}
        self._include_stack = []
        self._included_sources = set()
        self._source_defs = {}
        self._source_exports_decl = {}
        self._source_exports = {}
        self._source_internals = {}
        self._source_imports = {}
        self._public_symbols = {}
        self._export_decl_lines = {}

    def _preprocess(self, codigo: str, nombre_fuente: str) -> str:
        """Flujo privado de preprocesamiento."""
        self._reset_state()
        lineas_salida, mapa_salida = self._procesar_texto(codigo, nombre_fuente)
        lineas_salida, _ = self._organizar_externs(lineas_salida, mapa_salida)
        self._reset_state()
        return "\n".join(lineas_salida)

    def preprocess(self, codigo: str, nombre_fuente: str = "<string>") -> PreprocessResult:
        """Preprocesa código y retorna resultado con mapa de líneas."""
        self._reset_state()
        lineas_salida, mapa_salida = self._procesar_texto(codigo, nombre_fuente)
        lineas_salida, mapa_salida = self._organizar_externs(lineas_salida, mapa_salida)
        texto_salida = "\n".join(lineas_salida)
        if texto_salida:
            texto_salida += "\n"
        exports = {k: set(v) for k, v in self._source_exports.items()}
        internals = {k: set(v) for k, v in self._source_internals.items()}
        imports = {k: set(v) for k, v in self._source_imports.items()}
        return PreprocessResult(
            text=texto_salida,
            line_map=mapa_salida,
            exports=exports,
            internals=internals,
            imports=imports,
        )

    def preprocess_archivo(self, ruta: str) -> PreprocessResult:
        """Preprocesa un archivo completo."""
        ruta_absoluta = os.path.abspath(ruta)
        if not os.path.isfile(ruta_absoluta):
            raise IncludeError(f"Archivo no encontrado: '{ruta_absoluta}'")
        with open(ruta_absoluta, "r", encoding="utf-8-sig") as f:
            contenido = f.read()
        return self.preprocess(contenido, nombre_fuente=ruta_absoluta)


