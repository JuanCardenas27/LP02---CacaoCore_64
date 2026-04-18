
import re
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
        # → output_text es el listado formateado para mostrar en ll_loaded
        # → la RAM global ya tiene los bytes escritos
    """

    # Expresiones regulares para los marcadores
    _RE_BRACE  = re.compile(r'\{(\d+)\}([0-9a-fA-F]*)')   # {N}hexresto
    _RE_BRACK  = re.compile(r'\[(\d+)\](-)?')              # [N] o [N]-

    def __init__(self):
        self._data_words: list[str] = []   # palabras hex del .data (sin resolver)
        self._text_words: list[str] = []   # palabras hex del .text (pueden tener marcadores)
        self._base_addr:  int       = 0
        self._data_addrs: list[int] = []   # dirección absoluta de cada variable .data
        self._text_addrs: list[int] = []   # dirección absoluta de cada instrucción .text

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
    # Paso 1: Parseo
    # ------------------------------------------------------------------

    def _parse(self, text: str) -> None:
        """Divide el texto en secciones .data y .text y extrae las palabras hex."""
        self._data_words = []
        self._text_words = []

        section = None
        for raw_line in text.splitlines():
            line = raw_line.strip()

            # Ignorar vacías y comentarios
            if not line or line.startswith('#'):
                continue

            lower = line.lower()
            if lower == '.data':
                section = 'data'
                continue
            if lower == '.text':
                section = 'text'
                continue

            if section == 'data':
                # Cada línea es una palabra hex de 64 bits (16 nibbles)
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
        1. {N}XXXXXXXX  →  dirección de instrucción N en los 3 primeros bytes
        2. [N]          →  dirección de variable N en bytes [2..4] (6 nibbles)
        3. [N]-XX       →  modo dash: nibble alto de dirección fusionado con byte siguiente
        """
        # ── Caso 1: {N}hexresto ──────────────────────────────────────────
        m_brace = self._RE_BRACE.match(word)
        if m_brace:
            instr_idx = int(m_brace.group(1))
            rest_hex  = m_brace.group(2)

            if instr_idx >= len(self._text_addrs):
                raise LinkerError(
                    f"Referencia {{N}} a instrucción {instr_idx} fuera de rango "
                    f"(total instrucciones: {len(self._text_addrs)})"
                )

            target_addr = self._text_addrs[instr_idx]
            # 3 bytes little-endian de la dirección destino
            addr_bytes = self._addr_to_3bytes_le(target_addr)

            # Rellenar el resto hasta 8 bytes totales
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
        # Expandir todos los [N] a sus nibbles de dirección
        # Detectar si hay modo dash
        result = word

        # Encontrar todos los [N] con posible '-' siguiendo
        def replace_bracket(m: re.Match) -> str:
            var_idx  = int(m.group(1))

            if var_idx >= len(self._data_addrs):
                raise LinkerError(
                    f"Referencia [N] a variable {var_idx} fuera de rango "
                    f"(total variables: {len(self._data_addrs)})"
                )

            addr = self._data_addrs[var_idx]
            # 3 bytes little-endian → 6 nibbles hex
            addr_bytes = self._addr_to_3bytes_le(addr)
            addr_hex6  = addr_bytes.hex()          # 6 nibbles, LE
            
            return addr_hex6

        result = self._RE_BRACK.sub(replace_bracket, result)

        if '-' in result:
            print('-------------')
            
            i = result.find('-')
            result_end = result[0:i]
            result_start = result[i+1:]
            address = result_end[1:i-1]
            address = "".join([address[ind] + address[ind+1] for ind in range(len(address)-1, -1, -1) if ind%2 == 0])
            address = result[i-1] + address + result[0]
            address = "".join([address[ind] + address[ind+1] for ind in range(len(address)-1, -1, -1) if ind%2 == 0])
            result = address + result_start
        # Validar longitud (debe ser exactamente 16 nibbles)
        if len(result) != 16:
            
            raise LinkerError(
                f"Longitud incorrecta tras resolver marcadores: '{word}' → '{result}' "
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

        # Asegurarse de que la zona de código NO esté protegida durante la carga
        ram.unprotect_code()

        # Cargar .data en la zona de datos estáticos
        for i, word_bytes in enumerate(resolved_data):
            addr = self._data_addrs[i]
            ram.write(addr, word_bytes)

        # Cargar .text en la zona de código
        for i, word_bytes in enumerate(resolved_text):
            addr = self._text_addrs[i]
            # Verificar que caiga dentro de la zona de código
            if not (addr):
                raise LinkerError(
                    f"Instrucción {i} en dirección 0x{addr:08X} fuera de la zona "
                    f"de código (0x{CODE_START:08X}–0x{CODE_END-1:08X})"
                )
            ram.write(addr, word_bytes)

        # Activar protección de código tras la carga
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

        Ejemplo: 0x00001000 → b'\\x00\\x10\\x00'
        """
        b0 = addr & 0xFF
        b1 = (addr >> 8)  & 0xFF
        b2 = (addr >> 16) & 0xFF
        b3 = (addr >> 32) & 0xFF
        return bytes([b0, b1, b2, b3])
