import re
import os
from memoria.ram import ram, DATA_START, CODE_START, CODE_END, WORD_SIZE


# ---------------------------------------------------------------------------
# Excepción propia
# ---------------------------------------------------------------------------

class LinkerError(Exception):
    """Error durante el enlazado o carga."""


# ---------------------------------------------------------------------------
# Clase Linker
# ---------------------------------------------------------------------------

class Linker:
    """
    Enlazador y cargador del CacaoCore-64.

    Uso típico (desde la GUI)
    --------------------------
        linker = Linker()
        output_text = linker.link_and_load(reloc_text, base_address=0x00001000)
        # -> output_text es el listado formateado para mostrar en ll_loaded
        # -> la RAM global ya tiene los bytes escritos
    """

    # Expresiones regulares para los marcadores
    _RE_BRACE = re.compile(r'\{(\d+)\}([0-9a-fA-F]*)')   # {N}hexresto
    _RE_BRACK = re.compile(r'\[(\d+)\](-)?')              # [N] o [N]-

    # Directivas de importación y declaración de externos
    _RE_IMPORT = re.compile(r'^\.import\s+"([^"]+)"', re.IGNORECASE)
    _RE_EXTERN = re.compile(r'^\.extern\s+(\S+)',     re.IGNORECASE)

    # Llamada a función externa:  "@func NombreFuncion"XXXXXX
    _RE_FUNC_CALL = re.compile(r'"@func\s+([^"]+)"([0-9a-fA-F]*)')

    # Definición de función en archivo de librería: cabecera tras token @func
    # El token que sigue a @func tiene la forma: NOMBRE{offset}
    _RE_FUNC_DEF = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\{(\d+)\}$')

    def __init__(self):
        self._data_words: list[str] = []   # palabras hex del .data (sin resolver)
        self._text_words: list[str] = []   # palabras hex del .text (pueden tener marcadores)
        self._base_addr:  int = 0
        self._data_addrs: list[int] = []   # dirección absoluta de cada variable .data
        self._text_addrs: list[int] = []   # dirección absoluta de cada instrucción .text

        # Importaciones: nombre_funcion -> índice absoluto en self._text_words
        self._func_index: dict[str, int] = {}

        self._lib_files: dict[str, str] = {
            "math.lib": "lib_vectores.reloc",
        }

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

    def link_and_load(self, reloc_text: str, base_address: int) -> str:
        """
        Procesa el código relocalizable, escribe en la RAM global y retorna
        el listado de código cargado.

        Parámetros
        ----------
        reloc_text   : str  Texto completo del código relocalizable.
        base_address : int  Dirección base para la sección .text.

        Retorna
        -------
        str  Listado legible de las palabras cargadas con sus direcciones.

        Lanza
        -----
        LinkerError  Si hay errores de formato, índices fuera de rango, etc.
        """
        self._base_addr = base_address
        self._parse(reloc_text)
        self._compute_addresses()
        resolved_data, resolved_text = self._resolve()
        self._load_into_ram(resolved_data, resolved_text)
        return self._format_output(resolved_data, resolved_text)

    # ------------------------------------------------------------------
    # Paso 0: Carga de librerías
    # ------------------------------------------------------------------

    def _load_library(self, lib_filename: str, extern_names: list[str]) -> None:
        """
        Lee ../Libraries/<lib_filename>, extrae sólo las funciones indicadas
        en extern_names y las añade al final de self._text_words.
        También actualiza self._func_index con el índice de primera instrucción
        de cada función importada.

        Los marcadores internos {N} de la librería usan índices absolutos
        relativos al inicio del archivo de librería. Al pegar las funciones al
        final del .text principal, recalculamos esos índices sumando el offset
        de inserción.

        Parámetros
        ----------
        lib_filename : str        Nombre del archivo (p.ej. "math.lib").
        extern_names : list[str]  Nombres de funciones a importar.
        """
        lib_path = os.path.join(
            os.path.dirname(__file__), '..', 'Libraries', lib_filename
        )
        try:
            with open(lib_path, 'r', encoding='utf-8') as fh:
                lib_text = fh.read()
        except FileNotFoundError:
            raise LinkerError(f"Librería no encontrada: '{lib_path}'")
        except OSError as exc:
            raise LinkerError(f"Error al leer librería '{lib_path}': {exc}")

        # ── Parsear funciones de la librería ──────────────────────────────
        # Tokenizar: cada token es una palabra o un @func NOMBRE{offset}
        tokens = lib_text.split()

        # Primero construir el mapa completo: nombre_func -> índice_en_tokens_de_instrucciones
        # Para ello necesitamos separar tokens @func de instrucciones.
        # Reconstruimos la lista lineal de instrucciones y el mapa de offsets.
        lib_instructions: list[str] = []   # todas las instrucciones en orden
        lib_func_offsets: dict[str, int] = {}  # nombre -> índice en lib_instructions

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == '@func':
                # Siguiente token es NOMBRE{offset}
                if i + 1 >= len(tokens):
                    raise LinkerError("Definición @func incompleta en librería.")
                header = tokens[i + 1]
                m = self._RE_FUNC_DEF.match(header)
                if not m:
                    raise LinkerError(
                        f"Cabecera de función inválida en librería: '{header}'"
                    )
                func_name = m.group(1)
                # El offset {N} es el índice absoluto dentro de lib_instructions
                # donde empieza esta función. Lo usamos sólo para validar.
                stated_offset = int(m.group(2))
                # Registramos el offset real (puede diferir del enunciado si el
                # formato de la librería no tiene instrucciones previas al primer @func)
                lib_func_offsets[func_name] = len(lib_instructions)
                i += 2
            else:
                lib_instructions.append(token)
                i += 1

        # ── Importar sólo las funciones pedidas en .extern ─────────────────
        # Determinar qué funciones necesitamos y en qué orden aparecen en la lib
        missing = [n for n in extern_names if n not in lib_func_offsets]
        if missing:
            raise LinkerError(
                f"Funciones no encontradas en '{lib_filename}': {missing}"
            )

        # Para cada función extern, extraer sus instrucciones (desde su offset
        # hasta el offset de la siguiente función, o fin).
        # Necesitamos el mapa ordenado por offset para saber los límites.
        sorted_funcs = sorted(lib_func_offsets.items(), key=lambda x: x[1])
        func_end: dict[str, int] = {}
        for idx, (fname, fstart) in enumerate(sorted_funcs):
            if idx + 1 < len(sorted_funcs):
                func_end[fname] = sorted_funcs[idx + 1][1]
            else:
                func_end[fname] = len(lib_instructions)

        # Offset de inserción en el .text principal
        insert_offset = len(self._text_words)

        # Añadir funciones en el orden en que aparecen en la librería
        # (para que los {N} internos entre ellas sean consistentes)
        for func_name, lib_start in sorted_funcs:
            if func_name not in extern_names:
                continue

            abs_index_in_main = insert_offset + (lib_start - lib_func_offsets[sorted_funcs[0][0]])

            # Calcular el offset de esta función relativo al punto de inserción
            # Recalcular teniendo en cuenta cuántas instrucciones de funciones
            # previas ya se insertaron.
            # Usamos un acumulador local.
            pass

        # Segundo paso: insertar instrucciones en orden de aparición en la lib,
        # ajustando {N} para que apunten al índice correcto en el .text principal.

        # Construir lista de (func_name, [instrucciones]) en orden de la lib
        funcs_to_insert = [
            (fname, lib_instructions[lib_func_offsets[fname]: func_end[fname]])
            for fname, _ in sorted_funcs
            if fname in extern_names
        ]

        # Calcular offsets finales en el .text principal para cada función
        # (necesario para ajustar {N} internos)
        final_offsets: dict[str, int] = {}
        cursor = insert_offset
        for fname, instrs in funcs_to_insert:
            final_offsets[fname] = cursor
            cursor += len(instrs)

        # Insertar instrucciones ajustando {N}
        for fname, instrs in funcs_to_insert:
            func_lib_start = lib_func_offsets[fname]  # índice en lib_instructions
            main_start = final_offsets[fname]      # índice en self._text_words

            for instr in instrs:
                adjusted = self._adjust_brace_refs(
                    instr,
                    lib_offset=func_lib_start,
                    main_offset=main_start,
                    lib_instructions=lib_instructions,
                    final_offsets=final_offsets,
                    lib_func_offsets=lib_func_offsets,
                )
                self._text_words.append(adjusted)

            # Registrar la dirección (índice) de la primera instrucción
            self._func_index[fname] = final_offsets[fname]

    def _adjust_brace_refs(
        self,
        instr: str,
        lib_offset: int,
        main_offset: int,
        lib_instructions: list[str],
        final_offsets: dict[str, int],
        lib_func_offsets: dict[str, int],
    ) -> str:
        """
        Reemplaza {N} dentro de una instrucción de librería:
        N es un índice absoluto en lib_instructions.
        Lo convertimos al índice absoluto correspondiente en self._text_words.

        La lógica es:
          - N apunta a la instrucción N de la librería.
          - Necesitamos saber a qué función pertenece esa instrucción N.
          - Si esa función está siendo importada, la nueva dirección es
            final_offsets[esa_funcion] + (N - lib_func_offsets[esa_funcion]).
          - Si no está siendo importada, es un error.
        """
        def replace_brace(m: re.Match) -> str:
            n = int(m.group(1))
            rest = m.group(2)

            # Determinar a qué función pertenece el índice N en la lib
            # (buscar la función cuyo rango [start, end) contiene N)
            sorted_starts = sorted(lib_func_offsets.items(), key=lambda x: x[1])
            owner_func = None
            owner_start = 0
            for fname, fstart in sorted_starts:
                if fstart <= n:
                    owner_func = fname
                    owner_start = fstart
                else:
                    break

            if owner_func is None:
                raise LinkerError(
                    f"Referencia {{N}} = {n} en librería no pertenece a ninguna función."
                )
            if owner_func not in final_offsets:
                raise LinkerError(
                    f"Referencia {{N}} = {n} apunta a función '{owner_func}' "
                    f"que no fue importada."
                )

            new_idx = final_offsets[owner_func] + (n - owner_start)
            return f'{{{new_idx}}}{rest}'

        return self._RE_BRACE.sub(replace_brace, instr)

    # ------------------------------------------------------------------
    # Paso 1: Parseo
    # ------------------------------------------------------------------

    def _parse(self, text: str) -> None:
        """
        Divide el texto en secciones .data y .text y extrae las palabras hex.
        Antes de parsear las secciones, procesa las directivas .import y .extern
        para cargar las funciones de librería al final del .text.
        """
        self._data_words = []
        self._text_words = []
        self._func_index = {}

        # ── Pre-parseo: recoger .import y .extern ──────────────────────
        import_files: list[str] = []
        extern_names: list[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            m_imp = self._RE_IMPORT.match(line)
            if m_imp:
                import_files.append(m_imp.group(1))
                continue
            m_ext = self._RE_EXTERN.match(line)
            if m_ext:
                extern_names.append(m_ext.group(1))

        # ── Parseo principal ────────────────────────────────────────────
        section = None
        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line or line.startswith('#'):
                continue

            # Saltar directivas ya procesadas
            if self._RE_IMPORT.match(line) or self._RE_EXTERN.match(line):
                continue

            lower = line.lower()
            if lower == '.data':
                section = 'data'
                continue
            if lower == '.text':
                section = 'text'
                continue

            if section == 'data':
                word = line.strip()
                if not self._is_valid_data_word(word):
                    raise LinkerError(
                        f"Palabra .data inválida: '{word}' "
                        f"(se esperan 16 nibbles hex sin prefijo)"
                    )
                self._data_words.append(word)

            elif section == 'text':
                word = line.strip()
                self._text_words.append(word)

        # ── Cargar funciones de librería al final del .text ─────────────
        if import_files and extern_names:
            for lib_file in import_files:
                self._load_library(self._lib_files.get(lib_file), extern_names)

    @staticmethod
    def _is_valid_data_word(word: str) -> bool:
        """Valida que sea exactamente 16 nibbles hexadecimales."""
        return bool(re.fullmatch(r'[0-9a-fA-F]{16}', word))

    # ------------------------------------------------------------------
    # Paso 2: Cálculo de direcciones absolutas
    # ------------------------------------------------------------------

    def _compute_addresses(self) -> None:
        """Calcula las direcciones absolutas de variables e instrucciones."""
        # Variables: inician en DATA_START, 8 bytes cada una
        self._data_addrs = [
            DATA_START + i * WORD_SIZE
            for i in range(len(self._data_words))
        ]

        # Instrucciones: inician en base_address, 8 bytes cada una
        self._text_addrs = [
            self._base_addr + i * WORD_SIZE
            for i in range(len(self._text_words))
        ]

    # ------------------------------------------------------------------
    # Paso 3: Resolución de marcadores
    # ------------------------------------------------------------------

    def _resolve(self) -> tuple[list[bytes], list[bytes]]:
        """
        Resuelve todos los marcadores en .text y convierte todas las palabras
        a bytes listos para cargar.

        Retorna
        -------
        (resolved_data, resolved_text)  listas de bytes de 8 bytes cada una.
        """
        resolved_data = [bytes.fromhex(w) for w in self._data_words]
        resolved_text = [self._resolve_word(word, idx)
                         for idx, word in enumerate(self._text_words)]

        return resolved_data, resolved_text

    def _resolve_word(self, word: str, word_idx: int) -> bytes:
        """
        Resuelve los marcadores en una sola palabra del .text.

        Casos manejados
        ---------------
        1. {N}XXXXXXXX        ->  dirección de instrucción N en los 3 primeros bytes
        2. [N]                ->  dirección de variable N en bytes [2..4] (6 nibbles)
        3. [N]-XX             ->  modo dash
        4. "@func Nombre"XXXX ->  dirección de primera instrucción de la función importada
        """
        # ── Caso 4: llamada a función importada ──────────────────────────
        m_call = self._RE_FUNC_CALL.match(word)
        if m_call:
            func_name = m_call.group(1).strip()
            rest_hex = m_call.group(2)

            if func_name not in self._func_index:
                raise LinkerError(
                    f"Función externa no resuelta: '{func_name}'. "
                    f"¿Falta .import o .extern?"
                )

            func_instr_idx = self._func_index[func_name]
            target_addr = self._text_addrs[func_instr_idx]
            addr_bytes = self._addr_to_3bytes_le(target_addr) # 3 bytes LE

            rest_bytes = bytes.fromhex(rest_hex.ljust(10, 'f'))[:5]
            word_bytes = addr_bytes + rest_bytes
            return word_bytes[:8]

        # ── Caso 1: {N}hexresto ──────────────────────────────────────────
        m_brace = self._RE_BRACE.match(word)
        if m_brace:
            instr_idx = int(m_brace.group(1))
            rest_hex = m_brace.group(2)

            if instr_idx >= len(self._text_addrs):
                raise LinkerError(
                    f"Referencia {{N}} a instrucción {instr_idx} fuera de rango "
                    f"(total instrucciones: {len(self._text_addrs)})"
                )

            target_addr = self._text_addrs[instr_idx]
            addr_bytes = self._addr_to_3bytes_le(target_addr)

            rest_bytes = bytes.fromhex(rest_hex.ljust(10, 'f'))[:5]
            word_bytes = addr_bytes + rest_bytes
            return word_bytes[:8]

        # ── Casos 2 y 3: contienen [N] ───────────────────────────────────
        if '[' in word:
            return self._resolve_bracket(word)

        # ── Sin marcadores: parsear directamente ─────────────────────────
        clean = word.replace('f', 'f')   # sin-op, por claridad
        try:
            raw = bytes.fromhex(clean)
        except ValueError:
            raise LinkerError(f"Palabra hex inválida en .text: '{word}'")

        if len(raw) != 8:
            raise LinkerError(
                f"Palabra del .text con longitud incorrecta: '{word}' "
                f"({len(raw)} bytes, se esperan 8)"
            )
        return raw

    def _resolve_bracket(self, word: str) -> bytes:
        """
        Resuelve una palabra que contiene uno o más marcadores [N] o [N]-.

        Formato observado en el ensamblador
        ------------------------------------
        Instrucción tipo MOVD con variable (sin registro):
            0200[0]39f0          (16 nibbles reemplazando posiciones 4-9)
            Posiciones de bytes: [0] op1  [1] op2  [2-4] addr  [5-7] relleno

        Instrucción tipo MOVD con variable y registro (modo dash):
            3[0]8-03ffff
            Aquí [0] ocupa 1 nibble de byte[0], y '-' indica que el
            nibble alto del byte siguiente se toma del nibble alto de la
            dirección de variable.

        La estrategia es trabajar a nivel de nibbles (caracteres hex).
        """
        result = word

        def replace_bracket(m: re.Match) -> str:
            var_idx = int(m.group(1))

            if var_idx >= len(self._data_addrs):
                raise LinkerError(
                    f"Referencia [N] a variable {var_idx} fuera de rango "
                    f"(total variables: {len(self._data_addrs)})"
                )

            addr = self._data_addrs[var_idx]
            addr_bytes = self._addr_to_3bytes_le(addr)
            addr_hex6 = addr_bytes.hex()

            return addr_hex6

        result = self._RE_BRACK.sub(replace_bracket, result)

        if '-' in result:
            print('-------------')

            i = result.find('-')
            result_end = result[0:i]
            result_start = result[i + 1:]
            address = result_end[1:i - 1]
            address = "".join(
                [address[ind] + address[ind + 1]
                 for ind in range(len(address) - 1, -1, -1) if ind % 2 == 0]
            )
            address = result[i - 1] + address + result[0]
            address = "".join(
                [address[ind] + address[ind + 1]
                 for ind in range(len(address) - 1, -1, -1) if ind % 2 == 0]
            )
            result = address + result_start

        if len(result) != 16:
            raise LinkerError(
                f"Longitud incorrecta tras resolver marcadores: '{word}' -> '{result}' "
                f"({len(result)} nibbles, se esperan 16)"
            )

        try:
            return bytes.fromhex(result)
        except ValueError:
            raise LinkerError(
                f"Resultado no es hex válido tras resolver marcadores: '{result}'"
            )

    # ------------------------------------------------------------------
    # Paso 4: Escritura en RAM
    # ------------------------------------------------------------------

    def _load_into_ram(
        self,
        resolved_data: list[bytes],
        resolved_text: list[bytes],
    ) -> None:
        """Escribe las secciones .data y .text en la RAM global."""

        ram.unprotect_code()

        for i, word_bytes in enumerate(resolved_data):
            addr = self._data_addrs[i]
            ram.write(addr, word_bytes)

        for i, word_bytes in enumerate(resolved_text):
            addr = self._text_addrs[i]
            if not (addr):
                raise LinkerError(
                    f"Instrucción {i} en dirección 0x{addr:08X} fuera de la zona "
                    f"de código (0x{CODE_START:08X}-0x{CODE_END-1:08X})"
                )
            ram.write(addr, word_bytes)

        ram.protect_code()

    # ------------------------------------------------------------------
    # Paso 5: Formateo del output
    # ------------------------------------------------------------------

    def _format_output(
        self,
        resolved_data: list[bytes],
        resolved_text: list[bytes],
    ) -> str:
        """
        Genera el texto que se mostrará en self.ll_loaded de la GUI.
        Formato por línea:  0x<ADDR>  <hex_word_16nibbles>
        """
        lines: list[str] = []

        if resolved_data:
            lines.append(".data")
            for i, word_bytes in enumerate(resolved_data):
                addr = self._data_addrs[i]
                lines.append(f"0x{addr:08X}  {word_bytes.hex()}")

        if resolved_text:
            lines.append(".text")
            for i, word_bytes in enumerate(resolved_text):
                addr = self._text_addrs[i]
                lines.append(f"0x{addr:08X}  {word_bytes.hex()}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    @staticmethod
    def _addr_to_3bytes_le(addr: int) -> bytes:
        """
        Extrae los 3 bytes menos significativos de una dirección de 32 bits
        en orden little-endian.

        Ejemplo: 0x00001000 -> b'\\x00\\x10\\x00'
        """
        b0 = addr & 0xFF
        b1 = (addr >> 8)  & 0xFF
        b2 = (addr >> 16) & 0xFF
        b3 = (addr >> 32) & 0xFF
        return bytes([b0, b1, b2, b3])