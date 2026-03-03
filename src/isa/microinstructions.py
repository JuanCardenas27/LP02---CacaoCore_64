"""
microinstructions.py — Especificaciones de Microinstrucciones de la ISA
========================================================================
Define el conjunto completo de instrucciones de la ISA junto con sus opcodes
de 64 bits para el procesador simulado de 64 bits.

Estructura del Opcode
---------------------
Cada opcode de 64 bits está codificado en hexadecimal. Los últimos 2 bits (los
menos significativos) codifican el modo de direccionamiento:

    - r  = 0b00  (registro)
    - i  = 0b01  (inmediato)
    - m  = 0b10  (memoria)
    - n  = 0b11  (ninguno/especial)

Categorías de Instrucciones
----------------------------
- Control: nop, hlt, ret, ei, di, iret, push, pop, int
- MOV: Movimiento de datos entre registros/memoria (diferentes tamaños)
- LOAD: Carga de datos desde memoria
- STORE: Almacenamiento de datos en memoria
- SEXT: Extensión de signo
- Aritmética: add, sub, mul, div, inc, dec, neg
- Lógica: and, or, xor, not
- Otras ALU: cmp, test, desplazamientos (shl, shr, rol, ror), cmpz
- Saltos: jmp, jz, jnz, jc, jnc, js, jns, jo, jno, jl, jg, jge, jle, call

Uso
---
El decodificador (decoder.py) utiliza esta lista para construir un árbol de
decodificación y traducir secuencias de bytes en nombres de instrucciones.
"""

MICROINSTRUCTION_SPECS = [

    # =========================
    # Control
    # =========================

    {"name": "nop", "opcode": 0xFFFFFFFFFFFFFFF0},
    {"name": "hlt", "opcode": 0x0000000000000000},
    {"name": "ret", "opcode": 0xFFFFFFFFFFFFFFF2},
    {"name": "ei", "opcode": 0xFFFFFFFFFFFFFFF3},
    {"name": "di", "opcode": 0xFFFFFFFFFFFFFFF4},
    {"name": "iret", "opcode": 0xFFFFFFFFFFFFFFF5},

    {"name": "push_r", "opcode": 0xFFFFFFFFFFFFF40},
    {"name": "pop_r", "opcode": 0xFFFFFFFFFFFFF44},

    {"name": "int_i", "opcode": 0xFFFFFFFFFF45},

    # =========================
    # MOV
    # =========================

    {"name": "movb_rr", "opcode": 0xFFFFFFFFFFF000},
    {"name": "movb_ri", "opcode": 0xFFFFFFFF001},
    {"name": "movb_rm", "opcode": 0xFFFF002},
    {"name": "movb_rn", "opcode": 0xFFFFFFFFFFF003},
    {"name": "movb_mr", "opcode": 0xFFFF008},
    {"name": "movb_mi", "opcode": 0xF009},
    {"name": "movb_nr", "opcode": 0xFFFFFFFFFFF00C},

    {"name": "movh_rr", "opcode": 0xFFFFFFFFFFF010},
    {"name": "movh_ri", "opcode": 0xFFFFFFFF011},
    {"name": "movh_rm", "opcode": 0xFFFF012},
    {"name": "movh_rn", "opcode": 0xFFFFFFFFFFF013},
    {"name": "movh_mr", "opcode": 0xFFFF018},
    {"name": "movh_mi", "opcode": 0xF019},
    {"name": "movh_nr", "opcode": 0xFFFFFFFFFFF01C},

    {"name": "movw_rr", "opcode": 0xFFFFFFFFFFF020},
    {"name": "movw_ri", "opcode": 0xFFFFFFFF021},
    {"name": "movw_rm", "opcode": 0xFFFF022},
    {"name": "movw_rn", "opcode": 0xFFFFFFFFFFF023},
    {"name": "movw_mr", "opcode": 0xFFFF028},
    {"name": "movw_mi", "opcode": 0xF029},
    {"name": "movw_nr", "opcode": 0xFFFFFFFFFFF02C},

    {"name": "movd_rr", "opcode": 0xFFFFFFFFFFF030},
    {"name": "movd_ri", "opcode": 0xFFFFFFFF031},
    {"name": "movd_rm", "opcode": 0xFFFF032},
    {"name": "movd_rn", "opcode": 0xFFFFFFFFFFF033},
    {"name": "movd_mr", "opcode": 0xFFFF038},
    {"name": "movd_mi", "opcode": 0xF039},
    {"name": "movd_nr", "opcode": 0xFFFFFFFFFFF03C},

    {"name": "swap_r", "opcode": 0xFFFFFFFFFFFFF50},
    {"name": "swap_rr", "opcode": 0xFFFFFFFFFFF0D0},

    # =========================
    # LOAD
    # =========================

    {"name": "loadb_m", "opcode": 0xFFFFFF02},
    {"name": "loadb_i", "opcode": 0xFFFFFFFFFF01},
    {"name": "loadb_rm", "opcode": 0xFFFF042},
    {"name": "loadb_ri", "opcode": 0xFFFFFFFF041},

    {"name": "loadh_m", "opcode": 0xFFFFFF06},
    {"name": "loadh_i", "opcode": 0xFFFFFFFFFF05},
    {"name": "loadh_rm", "opcode": 0xFFFF052},
    {"name": "loadh_ri", "opcode": 0xFFFFFFFF051},

    {"name": "loadw_m", "opcode": 0xFFFFFF0A},
    {"name": "loadw_i", "opcode": 0xFFFFFFFFFF09},
    {"name": "loadw_rm", "opcode": 0xFFFF062},
    {"name": "loadw_ri", "opcode": 0xFFFFFFFF061},

    {"name": "loadd_m", "opcode": 0xFFFFFF0E},
    {"name": "loadd_i", "opcode": 0xFFFFFFFFFF0D},
    {"name": "loadd_rm", "opcode": 0xFFFF072},
    {"name": "loadd_ri", "opcode": 0xFFFFFFFF071},

    {"name": "lea_m", "opcode": 0xFFFFFF82},
    {"name": "lea_rm", "opcode": 0xFFFF152},

    # =========================
    # STORE
    # =========================

    {"name": "storeb_m", "opcode": 0xFFFFFF12},
    {"name": "storeb_r", "opcode": 0xFFFFFFFFFFFFF00},
    {"name": "storeb_mr", "opcode": 0xFFFF088},
    {"name": "storeb_mi", "opcode": 0xF049},

    {"name": "storeh_m", "opcode": 0xFFFFFF16},
    {"name": "storeh_r", "opcode": 0xFFFFFFFFFFFFF04},
    {"name": "storeh_mr", "opcode": 0xFFFF098},
    {"name": "storeh_mi", "opcode": 0xF059},

    {"name": "storew_m", "opcode": 0xFFFFFF1A},
    {"name": "storew_r", "opcode": 0xFFFFFFFFFFFFF08},
    {"name": "storew_mr", "opcode": 0xFFFF0A8},
    {"name": "storew_mi", "opcode": 0xF069},

    {"name": "stored_m", "opcode": 0xFFFFFF1E},
    {"name": "stored_r", "opcode": 0xFFFFFFFFFFFFF0C},
    {"name": "stored_mr", "opcode": 0xFFFF0B8},
    {"name": "stored_mi", "opcode": 0xF079},

    # =========================
    # SEXT
    # =========================

    {"name": "sext_ri", "opcode": 0xFFFFFFFF081},

    # =========================
    # Aritmética
    # =========================

    {"name": "add_m", "opcode": 0xFFFFF022},
    {"name": "add_r", "opcode": 0xFFFFFFFFFFFF010},
    {"name": "add_i", "opcode": 0xFFFFFFFFF011},
    {"name": "add_rr", "opcode": 0xFFFFFFFFFF0040},
    {"name": "add_ri", "opcode": 0xFFFFFFF0091},
    {"name": "add_rm", "opcode": 0xFFF00C2},
    {"name": "add_rn", "opcode": 0xFFFFFFFFFF0043},

    {"name": "sub_m", "opcode": 0xFFFFF126},
    {"name": "sub_r", "opcode": 0xFFFFFFFFFFFF114},
    {"name": "sub_i", "opcode": 0xFFFFFFFFF115},
    {"name": "sub_rr", "opcode": 0xFFFFFFFFFF1050},
    {"name": "sub_ri", "opcode": 0xFFFFFFF10A1},
    {"name": "sub_rm", "opcode": 0xFFF10D2},
    {"name": "sub_rn", "opcode": 0xFFFFFFFFFF1053},

    {"name": "mul_m", "opcode": 0xFFFFF32A},
    {"name": "mul_r", "opcode": 0xFFFFFFFFFFFF318},
    {"name": "mul_i", "opcode": 0xFFFFFFFFF319},
    {"name": "mul_rr", "opcode": 0xFFFFFFFFFF3060},
    {"name": "mul_ri", "opcode": 0xFFFFFFF30B1},
    {"name": "mul_rm", "opcode": 0xFFF30E2},
    {"name": "mul_rn", "opcode": 0xFFFFFFFFFF3063},

    {"name": "div_m", "opcode": 0xFFFFF42E},
    {"name": "div_r", "opcode": 0xFFFFFFFFFFFF41C},
    {"name": "div_i", "opcode": 0xFFFFFFFFF41D},
    {"name": "div_rr", "opcode": 0xFFFFFFFFFF4070},
    {"name": "div_ri", "opcode": 0xFFFFFFF40C1},
    {"name": "div_rm", "opcode": 0xFFF40F2},
    {"name": "div_rn", "opcode": 0xFFFFFFFFFF4073},

    {"name": "inc_r", "opcode": 0xFFFFFFFFFFFF220},
    {"name": "inc_m", "opcode": 0xFFFFF232},

    {"name": "dec_r", "opcode": 0xFFFFFFFFFFFF524},
    {"name": "dec_m", "opcode": 0xFFFFF536},

    {"name": "neg_r", "opcode": 0xFFFFFFFFFFFFF48},
    {"name": "neg_m", "opcode": 0xFFFFFF7A},

    # =========================
    # Lógica
    # =========================

    {"name": "and_m", "opcode": 0xFFFFF73A},
    {"name": "and_r", "opcode": 0xFFFFFFFFFFFF720},
    {"name": "and_i", "opcode": 0xFFFFFFFFF721},
    {"name": "and_rr", "opcode": 0xFFFFFFFFFF7080},
    {"name": "and_ri", "opcode": 0xFFFFFFF70D1},
    {"name": "and_rm", "opcode": 0xFFF7102},
    {"name": "and_rn", "opcode": 0xFFFFFFFFFF7083},

    {"name": "or_m", "opcode": 0xFFFFF83E},
    {"name": "or_r", "opcode": 0xFFFFFFFFFFFF82C},
    {"name": "or_i", "opcode": 0xFFFFFFFFF825},
    {"name": "or_rr", "opcode": 0xFFFFFFFFFF8090},
    {"name": "or_ri", "opcode": 0xFFFFFFF80E1},
    {"name": "or_rm", "opcode": 0xFFF8112},
    {"name": "or_rn", "opcode": 0xFFFFFFFFFF8093},

    {"name": "xor_m", "opcode": 0xFFFFF942},
    {"name": "xor_r", "opcode": 0xFFFFFFFFFFFF930},
    {"name": "xor_i", "opcode": 0xFFFFFFFFF929},
    {"name": "xor_rr", "opcode": 0xFFFFFFFFFF90A0},
    {"name": "xor_ri", "opcode": 0xFFFFFFF90F1},
    {"name": "xor_rm", "opcode": 0xFFF9122},
    {"name": "xor_rn", "opcode": 0xFFFFFFFFFF90A3},

    {"name": "not_r", "opcode": 0xFFFFFFFFFFFFA34},
    {"name": "not_m", "opcode": 0xFFFFFA46},

    # =========================
    # Otras relaciondas con ALU
    # =========================

    {"name": "cmp_m", "opcode": 0xFFFFF64A},
    {"name": "cmp_r", "opcode": 0xFFFFFFFFFFFF638},
    {"name": "cmp_i", "opcode": 0xFFFFFFFFF62D},
    {"name": "cmp_rr", "opcode": 0xFFFFFFFFFF60B0},
    {"name": "cmp_ri", "opcode": 0xFFFFFFF6101},
    {"name": "cmp_rm", "opcode": 0xFFF6132},
    {"name": "cmp_rn", "opcode": 0xFFFFFFFFFF60B3},

    {"name": "test_m", "opcode": 0xFFFFFD4E},
    {"name": "test_r", "opcode": 0xFFFFFFFFFFFFD3C},
    {"name": "test_i", "opcode": 0xFFFFFFFFFD31},
    {"name": "test_rr", "opcode": 0xFFFFFFFFFFD0C0},
    {"name": "test_ri", "opcode": 0xFFFFFFFD111},
    {"name": "test_rm", "opcode": 0xFFFD142},
    {"name": "test_rn", "opcode": 0xFFFFFFFFFFD0C3},

    {"name": "shl_i", "opcode": 0xFFFFFFFFFB35},
    {"name": "shl_ri", "opcode": 0xFFFFFFFB121},

    {"name": "shr_i", "opcode": 0xFFFFFFFFFC39},
    {"name": "shr_ri", "opcode": 0xFFFFFFFC131},

    {"name": "rol_i", "opcode": 0xFFFFFFFFFF3D},
    {"name": "rol_ri", "opcode": 0xFFFFFFFF141},

    {"name": "ror_i", "opcode": 0xFFFFFFFFFF41},
    {"name": "ror_ri", "opcode": 0xFFFFFFFF151},

    {"name": "cmpz_r", "opcode": 0xFFFFFFFFFFFFF4C},
    {"name": "cmpz_m", "opcode": 0xFFFFFF7E},

    # =========================
    # Saltos
    # =========================

    {"name": "jmp_m", "opcode": 0xFFFFFF52},
    {"name": "jz_m", "opcode": 0xFFFFFF56},
    {"name": "jnz_m", "opcode": 0xFFFFFF5A},
    {"name": "jc_m", "opcode": 0xFFFFFF5E},
    {"name": "jnc_m", "opcode": 0xFFFFFF62},
    {"name": "js_m", "opcode": 0xFFFFFF66},
    {"name": "jns_m", "opcode": 0xFFFFFF6A},
    {"name": "jo_m", "opcode": 0xFFFFFF6E},
    {"name": "jno_m", "opcode": 0xFFFFFF72},

    {"name": "jl_m", "opcode": 0xFFFFFF86},
    {"name": "jg_m", "opcode": 0xFFFFFF8E},
    {"name": "jge_m", "opcode": 0xFFFFFF92},
    {"name": "jle_m", "opcode": 0xFFFFFF96},

    {"name": "call_m", "opcode": 0xFFFFFF76}

]
