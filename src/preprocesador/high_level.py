import os
import sys
from typing import Dict, List, Optional, Tuple

from .errors import CondicionalError, IncludeError, MacroError, PreprocesadorError
from .lexer_high_level import build_lexer
from .models import Macro, PreprocessResult, SourceLine


class Preprocesador:
    def __init__(
        self,
        max_macro_expansion: int = 50,
        macros_iniciales: Optional[Dict[str, str]] = None,
        verbose: bool = False,
    ):
        # Inicializa el preprocesador con estado vacío y configuración
        self.max_macro_expansion = max_macro_expansion
        self.verbose = verbose
        self.advertencias: List[str] = []

        self._defines: Dict[str, Macro] = {}
        self._pila_cond: List[bool] = []
        self._imports_set: set = set()
        self._externs_explicit: set = set()
        self._librerias_importadas: Dict[str, str] = {}  # calificador (e.g. "math.lib") -> nombre_archivo
        self._funciones_por_libreria: Dict[str, List[Tuple[str, int]]] = {}  # libreria -> [(nombre, linea)]

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
        funcs = [f.strip() for f in lista.split(",") if f.strip()]
        return nombre, funcs if funcs else None

    def _parsear_nombre_macro(self, linea_raw: str, dir_name: str) -> str:
        """Extrae nombre de macro de directivas."""
        payload = self._extraer_payload_directiva(linea_raw, dir_name)
        idx = 0
        while idx < len(payload) and payload[idx].isspace(): idx += 1
        nombre, _ = self._leer_identificador(payload, idx)
        if not nombre: raise PreprocesadorError(f"#{dir_name} inválido: {linea_raw}")
        return nombre

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

    def _procesar_tokens(
        self, texto: str, fuente: str
    ) -> Tuple[List[str], List[SourceLine]]:
        """FUNCIÓN CENTRAL DE PREPROCESAMIENTO: Implementa el algoritmo de dos pasadas con PLY Lex.
        
        ARQUITECTURA DE DOS PASADAS:
        
        PRIMERA PASADA (Tokenización + Procesamiento):
        1. Usa PLY Lex para tokenizar entrada separando directivas de código
        2. Procesa directivas: #include, #define, #ifdef, #ifndef, #else, #endif, #undef, #error, #warning
        3. Mantiene pila de condicionales para #ifdef/#ifndef/#endif anidados
        4. Detecta y expande macros (simples como PI y parametrizadas como SQUARE(x))
        5. Detecta funciones calificadas: math.lib.sqrt → registra para auto-import
        6. Reemplaza llamadas calificadas por simples: math.lib.sqrt() → sqrt()
        
        SEGUNDA PASADA (Reorganización):
        7. Agrupa .extern bajo sus .import correspondientes
        8. Evita duplicados de .extern
        9. Mantiene mapa de trazabilidad para debugging (SourceLine)
        
        Args:
            texto: Código fuente completo (con directivas de preprocesador)
            fuente: Nombre del archivo para traceabilidad de errores
            
        Returns:
            (lineas_salida, mapa_salida): Código procesado sin directivas + metadata de líneas
            
        Raises:
            PreprocesadorError: Errores sintácticos en directivas
            CondicionalError: #endif sin #ifdef o pila de condicionales desequilibrada"""
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

        # Primera pasada: procesar directivas, acumular funciones calificadas, procesar código
        
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
                    self._emit_import(
                        nombre_archivo,
                        lineas_salida,
                        mapa_salida,
                        fuente,
                        numero_linea,
                    )
                    # Registrar librería para detección de llamadas calificadas
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

            # Es línea de código
            linea_expandida = self._expandir_macros(linea_original)
            
            # Detectar funciones calificadas (para procesar después)
            funciones_calificadas = self._extractar_funciones_calificadas(linea_expandida)
            for clave_calificada, nombre_funcion in funciones_calificadas.items():
                # clave_calificada formato: "math.lib.sqrt" → extraer librería "math.lib"
                partes = clave_calificada.rsplit(".", 1)
                if len(partes) == 2:
                    nombre_libreria = partes[0]
                    nombre_normalizado = nombre_funcion.lower()
                    if nombre_normalizado not in self._externs_explicit:
                        if nombre_libreria not in self._funciones_por_libreria:
                            self._funciones_por_libreria[nombre_libreria] = []
                        self._funciones_por_libreria[nombre_libreria].append((nombre_funcion, numero_linea))
            
            # Reemplazar llamadas calificadas por llamadas simples
            linea_reemplazada = self._reemplazar_funciones_calificadas(linea_expandida)
            
            if linea_reemplazada.strip():
                lineas_salida.append(linea_reemplazada.rstrip())
                mapa_salida.append(SourceLine(path=fuente, line=numero_linea))

        if self._pila_cond:
            raise CondicionalError(
                f"Faltan {len(self._pila_cond)} directiva(s) #endif", fuente
            )

        # Segunda pasada: insertar .extern debajo de su correspondiente .import
        # Procesar líneas para insertar .extern después de su .import
        lineas_salida_organizada = []
        mapa_salida_organizada = []
        
        i = 0
        while i < len(lineas_salida):
            linea_actual = lineas_salida[i]
            lineas_salida_organizada.append(linea_actual)
            mapa_salida_organizada.append(mapa_salida[i])
            
            # Si es un .import, insertar los .extern de esa librería
            if linea_actual.startswith('.import "'):
                # Extraer nombre de la librería: .import "math.lib" → math.lib
                nombre_lib_with_quotes = linea_actual[9:]  # Skip '.import "'
                nombre_lib = nombre_lib_with_quotes.rstrip('"')
                
                # Insertar .extern para esta librería si existen
                if nombre_lib in self._funciones_por_libreria:
                    # Obtener funciones únicas para esta librería (evitar duplicados)
                    funciones_vistas = set()
                    for nombre_funcion, numero_linea in sorted(self._funciones_por_libreria[nombre_lib], key=lambda x: x[0]):
                        nombre_normalizado = nombre_funcion.lower()
                        if nombre_normalizado not in self._externs_explicit and nombre_normalizado not in funciones_vistas:
                            lineas_salida_organizada.append(f".extern {nombre_funcion}")
                            mapa_salida_organizada.append(SourceLine(path=fuente, line=numero_linea))
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

    def _preprocess(self, codigo: str, nombre_fuente: str) -> str:
        """Flujo privado de preprocesamiento."""
        self._reset_state()
        lineas_salida, _ = self._procesar_tokens(codigo, nombre_fuente)
        self._reset_state()
        return "\n".join(lineas_salida)

    def preprocess(self, codigo: str, nombre_fuente: str = "<string>") -> PreprocessResult:
        """Preprocesa código y retorna resultado con mapa de líneas."""
        self._reset_state()
        lineas_salida, mapa_salida = self._procesar_tokens(codigo, nombre_fuente)
        texto_salida = "\n".join(lineas_salida)
        if texto_salida:
            texto_salida += "\n"
        return PreprocessResult(text=texto_salida, line_map=mapa_salida)

    def preprocess_archivo(self, ruta: str) -> PreprocessResult:
        """Preprocesa un archivo completo."""
        ruta_absoluta = os.path.abspath(ruta)
        if not os.path.isfile(ruta_absoluta):
            raise IncludeError(f"Archivo no encontrado: '{ruta_absoluta}'")
        with open(ruta_absoluta, "r", encoding="utf-8-sig") as f:
            contenido = f.read()
        return self.preprocess(contenido, nombre_fuente=ruta_absoluta)


