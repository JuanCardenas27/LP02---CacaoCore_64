"""
Analizador Léxico para Módulos Objeto (Formato .obj)
====================================================
Usa PLY (Python Lex-Yacc) para analizar archivos de módulos objeto.

Formato esperado:
  [MODULE nombre_modulo]
  [CODE] bytes_codigo_en_hex
  [DATA] bytes_datos_en_hex
  [SYMBOLS] nombre:tipo:valor,nombre:tipo:valor,...
  [EXTERNAL] nombre:posicion:tipo,nombre:posicion:tipo,...

Ejemplo:
  [MODULE main]
  [CODE] 48 89 C3 FF E0
  [DATA] 00 01 02 03
  [SYMBOLS] inicio:code:0x1000,fin:code:0x2000
  [EXTERNAL] funcion_externa:0x500:32bits
"""

import ply.lex as lex
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class Simbolo:
    nombre: str
    tipo: str  # 'code', 'data', 'function'
    valor: int


@dataclass
class ReferenciaExterna:
    nombre: str
    posicion: int
    tipo: str  # '32bits', '16bits', '8bits'


class AnalizadorModulos:
    """Analizador léxico para archivos de módulos objeto"""

    tokens = (
        'MODULE', 'CODE', 'DATA', 'SYMBOLS', 'EXTERNAL',
        'LBRACKET', 'RBRACKET', 'WORD', 'HEX', 'COLON', 'COMMA',
        'NEWLINE', 'ERROR_TOKEN'
    )

    reserved = {
        'MODULE': 'MODULE',
        'CODE': 'CODE',
        'DATA': 'DATA',
        'SYMBOLS': 'SYMBOLS',
        'EXTERNAL': 'EXTERNAL'
    }

    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_COLON = r':'
    t_COMMA = r','
    t_ignore = ' \t'

    def __init__(self) -> None:
        self.lexer = lex.lex(module=self)
        self.lineno = 1

    @staticmethod
    def t_HEX(t):
        r'[0-9A-Fa-f]{1,2}(?=[\s,\]\)])'
        t.value = int(t.value, 16)
        return t

    @staticmethod
    def t_WORD(t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = AnalizadorModulos.reserved.get(t.value, 'WORD')
        return t

    @staticmethod
    def t_newline(t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    @staticmethod
    def t_error(t):
        print(f"Error léxico: carácter inesperado '{t.value[0]}' en línea {t.lexer.lineno}")
        t.type = 'ERROR_TOKEN'
        t.lexer.skip(1)
        return t

    def parse_module(self, content: str) -> Dict:
        """
        Analiza un archivo de módulo objeto completo.
        
        Retorna diccionario con:
        {
            'nombre': str,
            'codigo': bytearray,
            'datos': bytearray,
            'simbolos': {nombre: Simbolo},
            'referencias_externas': {nombre: [ReferenciaExterna]}
        }
        """
        self.lexer.input(content)
        self.lineno = 1

        result = {
            'nombre': None,
            'codigo': bytearray(),
            'datos': bytearray(),
            'simbolos': {},
            'referencias_externas': {}
        }

        # Parsing simple basado en secciones
        lines = content.strip().split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            if line.startswith('[MODULE'):
                # Extrae el nombre: [MODULE nombre]
                parts = line.split()
                if len(parts) >= 2:
                    result['nombre'] = parts[1].rstrip(']')

            elif line.startswith('[CODE]'):
                current_section = 'CODE'
                hex_part = line[6:].strip()
                if hex_part:
                    result['codigo'].extend(self._parse_hex_string(hex_part))

            elif line.startswith('[DATA]'):
                current_section = 'DATA'
                hex_part = line[6:].strip()
                if hex_part:
                    result['datos'].extend(self._parse_hex_string(hex_part))

            elif line.startswith('[SYMBOLS]'):
                current_section = 'SYMBOLS'
                symbols_part = line[9:].strip()
                if symbols_part:
                    self._parse_symbols(symbols_part, result['simbolos'])

            elif line.startswith('[EXTERNAL]'):
                current_section = 'EXTERNAL'
                external_part = line[10:].strip()
                if external_part:
                    self._parse_external(external_part, result['referencias_externas'])

            elif current_section == 'CODE':
                result['codigo'].extend(self._parse_hex_string(line))

            elif current_section == 'DATA':
                result['datos'].extend(self._parse_hex_string(line))

        return result

    @staticmethod
    def _parse_hex_string(hex_str: str) -> bytearray:
        """Convierte una cadena de hex separados por espacios a bytearray"""
        result = bytearray()
        for byte_str in hex_str.split():
            byte_str = byte_str.strip()
            if byte_str and len(byte_str) <= 2:
                try:
                    result.append(int(byte_str, 16))
                except ValueError:
                    pass
        return result

    @staticmethod
    def _parse_symbols(symbols_str: str, target_dict: Dict[str, Simbolo]) -> None:
        """Parsea la sección de símbolos: nombre:tipo:valor,nombre:tipo:valor,..."""
        for item in symbols_str.split(','):
            item = item.strip()
            if ':' in item:
                parts = item.split(':')
                if len(parts) >= 3:
                    nombre = parts[0].strip()
                    tipo = parts[1].strip()
                    try:
                        # Intenta parsear como hex o decimal
                        valor_str = parts[2].strip()
                        if valor_str.startswith('0x') or valor_str.startswith('0X'):
                            valor = int(valor_str, 16)
                        else:
                            valor = int(valor_str)
                        target_dict[nombre] = Simbolo(nombre, tipo, valor)
                    except ValueError:
                        pass

    @staticmethod
    def _parse_external(external_str: str, target_dict: Dict[str, List[ReferenciaExterna]]) -> None:
        """Parsea referencias externas: nombre:posicion:tipo,nombre:posicion:tipo,..."""
        for item in external_str.split(','):
            item = item.strip()
            if ':' in item:
                parts = item.split(':')
                if len(parts) >= 3:
                    nombre = parts[0].strip()
                    try:
                        posicion_str = parts[1].strip()
                        if posicion_str.startswith('0x') or posicion_str.startswith('0X'):
                            posicion = int(posicion_str, 16)
                        else:
                            posicion = int(posicion_str)
                        tipo = parts[2].strip()

                        ref = ReferenciaExterna(nombre, posicion, tipo)
                        if nombre not in target_dict:
                            target_dict[nombre] = []
                        target_dict[nombre].append(ref)
                    except ValueError:
                        pass


# Instancia global
analizador_modulos = AnalizadorModulos()


if __name__ == '__main__':
    sample_module = '''
// Módulo principal
[MODULE main]
[CODE] 48 89 C3 FF E0 90 90
[DATA] 00 01 02 03 04 05
[SYMBOLS] inicio:code:0x1000,fin:code:0x1007,var1:data:0x2000
[EXTERNAL] funcion_externa:0x5:32bits,otra_funcion:0xA:16bits
'''

    parser = AnalizadorModulos()
    result = parser.parse_module(sample_module)

    print("Módulo:", result['nombre'])
    print("Código:", result['codigo'].hex())
    print("Datos:", result['datos'].hex())
    print("Símbolos:")
    for nom, sim in result['simbolos'].items():
        print(f"  {nom}: {sim.tipo} = 0x{sim.valor:X}")
    print("Referencias externas:")
    for nom, refs in result['referencias_externas'].items():
        for ref in refs:
            print(f"  {nom} @ 0x{ref.posicion:X} ({ref.tipo})")
