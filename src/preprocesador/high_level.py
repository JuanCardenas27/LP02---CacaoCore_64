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

    def _activo(self) -> bool:
        return all(self._pila_cond) if self._pila_cond else True

    def _log(self, msg: str):
        if self.verbose:
            print(f"[PREPROCESADOR] {msg}", file=sys.stderr)

    def _advertir(self, msg: str, archivo: str = None, linea: int = None):
        ubicacion = f"{archivo}:{linea}" if archivo else "<string>"
        entrada = f"[ADVERTENCIA] {ubicacion}: {msg}"
        self.advertencias.append(entrada)
        print(entrada, file=sys.stderr)

    def _es_inicio_identificador(self, caracter: str) -> bool:
        return caracter.isalpha() or caracter == "_"

    def _es_identificador(self, caracter: str) -> bool:
        return caracter.isalnum() or caracter == "_"

    def _saltar_espacios(self, texto: str, indice: int) -> int:
        while indice < len(texto) and texto[indice].isspace():
            indice += 1
        return indice

    def _leer_identificador(self, texto: str, indice: int) -> Tuple[str, int]:
        if indice >= len(texto) or not self._es_inicio_identificador(texto[indice]):
            return "", indice
        inicio = indice
        indice += 1
        while indice < len(texto) and self._es_identificador(texto[indice]):
            indice += 1
        return texto[inicio:indice], indice

    def _extraer_payload_directiva(self, linea_raw: str, nombre_directiva: str) -> str:
        linea_sin_comentario = self._strip_comment(linea_raw)
        linea_limpia = linea_sin_comentario.lstrip()
        if not linea_limpia.startswith("#"):
            raise PreprocesadorError(f"Sintaxis #{nombre_directiva} invalida: {linea_raw}")

        contenido = linea_limpia[1:].lstrip()
        if not contenido.startswith(nombre_directiva):
            raise PreprocesadorError(f"Sintaxis #{nombre_directiva} invalida: {linea_raw}")

        return contenido[len(nombre_directiva):].lstrip()

    def _obtener_nombre_directiva(self, linea_raw: str) -> Optional[str]:
        linea_sin_comentario = self._strip_comment(linea_raw)
        linea_limpia = linea_sin_comentario.lstrip()
        if not linea_limpia.startswith("#"):
            return None

        indice = self._saltar_espacios(linea_limpia, 1)
        nombre_directiva, _ = self._leer_identificador(linea_limpia, indice)
        return nombre_directiva

    def _leer_argumentos_parentesis(
        self, texto: str, indice_parentesis: int
    ) -> Tuple[Optional[List[str]], int]:
        if indice_parentesis >= len(texto) or texto[indice_parentesis] != "(":
            return None, indice_parentesis

        profundidad = 0
        argumentos: List[str] = []
        buffer_actual: List[str] = []
        indice = indice_parentesis

        while indice < len(texto):
            caracter = texto[indice]
            if caracter == "(":
                profundidad += 1
                if profundidad > 1:
                    buffer_actual.append(caracter)
            elif caracter == ")":
                profundidad -= 1
                if profundidad == 0:
                    argumentos.append("".join(buffer_actual).strip())
                    argumentos = [arg for arg in argumentos if arg]
                    return argumentos, indice + 1
                buffer_actual.append(caracter)
            elif caracter == "," and profundidad == 1:
                argumentos.append("".join(buffer_actual).strip())
                buffer_actual = []
            else:
                buffer_actual.append(caracter)
            indice += 1

        return None, indice_parentesis

    def _parsear_define(self, linea_raw: str) -> Macro:
        cuerpo_define = self._extraer_payload_directiva(linea_raw, "define")
        indice = self._saltar_espacios(cuerpo_define, 0)
        nombre_macro, indice = self._leer_identificador(cuerpo_define, indice)
        if not nombre_macro:
            raise MacroError(f"Sintaxis #define invalida: {linea_raw}")

        indice = self._saltar_espacios(cuerpo_define, indice)
        parametros: Optional[List[str]] = None
        if indice < len(cuerpo_define) and cuerpo_define[indice] == "(":
            parametros, indice = self._leer_argumentos_parentesis(cuerpo_define, indice)
            if parametros is None:
                raise MacroError(f"Sintaxis #define invalida: {linea_raw}")

        valor_macro = cuerpo_define[indice:].strip()
        if parametros is None:
            valor_macro = valor_macro or "1"

        return Macro(nombre_macro, valor_macro, parametros)

    def _parsear_include(self, linea_raw: str) -> Tuple[str, Optional[List[str]]]:
        payload = self._extraer_payload_directiva(linea_raw, "include")
        indice = self._saltar_espacios(payload, 0)
        if indice >= len(payload) or payload[indice] != "\"":
            raise IncludeError(f"Sintaxis #include invalida: {linea_raw}")

        indice += 1
        fin_nombre = payload.find("\"", indice)
        if fin_nombre == -1:
            raise IncludeError(f"Sintaxis #include invalida: {linea_raw}")

        nombre_archivo = payload[indice:fin_nombre]
        resto = payload[fin_nombre + 1:].strip()
        if not resto:
            return nombre_archivo, None

        if not resto.startswith("{"):
            raise IncludeError(f"Sintaxis #include invalida: {linea_raw}")

        fin_llave = resto.find("}")
        if fin_llave == -1:
            raise IncludeError(f"Sintaxis #include invalida: {linea_raw}")

        lista_funciones = resto[1:fin_llave].strip()
        if resto[fin_llave + 1:].strip():
            raise IncludeError(f"Sintaxis #include invalida: {linea_raw}")

        if not lista_funciones:
            raise IncludeError("Lista de funciones vacia en #include")

        funciones = [f.strip() for f in lista_funciones.split(",") if f.strip()]
        if not funciones:
            raise IncludeError("Lista de funciones vacia en #include")
        return nombre_archivo, funciones

    def _parsear_nombre_macro(self, linea_raw: str, nombre_directiva: str) -> str:
        payload = self._extraer_payload_directiva(linea_raw, nombre_directiva)
        indice = self._saltar_espacios(payload, 0)
        nombre_macro, _ = self._leer_identificador(payload, indice)
        if not nombre_macro:
            raise PreprocesadorError(
                f"Sintaxis #{nombre_directiva} invalida: {linea_raw}"
            )
        return nombre_macro

    def _find_comment_start(self, linea: str) -> Optional[int]:
        en_comilla_simple = False
        en_comilla_doble = False
        indice = 0
        while indice < len(linea):
            caracter = linea[indice]
            if caracter == "'" and not en_comilla_doble:
                en_comilla_simple = not en_comilla_simple
            elif caracter == '"' and not en_comilla_simple:
                en_comilla_doble = not en_comilla_doble
            elif not en_comilla_simple and not en_comilla_doble:
                if linea.startswith("//", indice):
                    return indice
            indice += 1
        return None

    def _strip_comment(self, line: str) -> str:
        indice_comentario = self._find_comment_start(line)
        return line[:indice_comentario] if indice_comentario is not None else line

    def _emit_import(
        self,
        nombre_lib: str,
        lineas_salida: List[str],
        mapa_salida: List[SourceLine],
        fuente: str,
        numero_linea: int,
    ) -> None:
        if nombre_lib in self._imports_set:
            return
        self._imports_set.add(nombre_lib)
        lineas_salida.append(f'.import "{nombre_lib}"')
        mapa_salida.append(SourceLine(path=fuente, line=numero_linea))



    def _extractar_funciones_calificadas(self, codigo: str) -> Dict[str, str]:
        """Extrae llamadas a funciones calificadas (e.g., math.lib.funcion).
        
        Retorna: Dict[calificador.función -> nombre_función]
        """
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
        """Reemplaza llamadas calificadas (math.lib.funcion) por funcion.
        
        Ejemplo: "math.lib.sqrt(9)" -> "sqrt(9)"
        """
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

    def _reemplazar_macro_parametrizada(self, codigo: str, macro_def: Macro) -> str:
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
        indice_comentario = self._find_comment_start(linea)
        codigo = linea[:indice_comentario] if indice_comentario is not None else linea
        comentario = linea[indice_comentario:] if indice_comentario is not None else ""

        for macro_def in self._defines.values():
            if macro_def.parametros is not None:
                codigo = self._reemplazar_macro_parametrizada(codigo, macro_def)

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
                    self._log(f"Libreria registrada para uso calificado: {nombre_archivo}")
                    
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
                        self._log(f"Macro definida: {macro}")
                    continue

                if nombre_directiva == "undef":
                    if self._activo():
                        nombre_macro = self._parsear_nombre_macro(
                            linea_original, "undef"
                        )
                        self._defines.pop(nombre_macro, None)
                        self._log(f"Macro eliminada: {nombre_macro}")
                    continue

                if nombre_directiva == "ifdef":
                    nombre_macro = self._parsear_nombre_macro(linea_original, "ifdef")
                    activo = nombre_macro in self._defines
                    self._pila_cond.append(activo)
                    self._log(
                        f"#ifdef {nombre_macro} -> {'activo' if activo else 'ignorado'}"
                    )
                    continue

                if nombre_directiva == "ifndef":
                    nombre_macro = self._parsear_nombre_macro(linea_original, "ifndef")
                    activo = nombre_macro not in self._defines
                    self._pila_cond.append(activo)
                    self._log(
                        f"#ifndef {nombre_macro} -> {'activo' if activo else 'ignorado'}"
                    )
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
                        mensaje = self._extraer_payload_directiva(
                            linea_original, "warning"
                        )
                        self._advertir(mensaje, fuente, numero_linea)
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
                            self._log(f"Función externa detectada: {nombre_funcion} (de {nombre_lib})")
            
            i += 1
        
        return lineas_salida_organizada, mapa_salida_organizada

    def _reset_state(self) -> None:
        self._defines = dict(self._macros_base)
        self._pila_cond = []
        self.advertencias = []
        self._imports_set = set()
        self._externs_explicit = set()
        self._librerias_importadas = {}
        self._funciones_por_libreria = {}

    def preprocess(self, codigo: str, nombre_fuente: str = "<string>") -> PreprocessResult:
        self._reset_state()

        lineas_salida, mapa_salida = self._procesar_tokens(codigo, nombre_fuente)

        texto_salida = "\n".join(lineas_salida)
        if texto_salida:
            texto_salida += "\n"

        return PreprocessResult(text=texto_salida, line_map=mapa_salida)

    def preprocess_archivo(self, ruta: str) -> PreprocessResult:
        ruta_absoluta = os.path.abspath(ruta)
        if not os.path.isfile(ruta_absoluta):
            raise IncludeError(f"Archivo no encontrado: '{ruta_absoluta}'")
        with open(ruta_absoluta, "r", encoding="utf-8-sig") as f:
            contenido_archivo = f.read()
        return self.preprocess(contenido_archivo, nombre_fuente=ruta_absoluta)


