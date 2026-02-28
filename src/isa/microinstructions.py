MICROINSTRUCTION_SPECS = [
    # Opcodes include addressing mode bits

    # =========================
    # Control
    # =========================

    {"name": "nop", "opcode": 0xFFFFFFFFFFFFFFF0},
    {"name": "hlt", "opcode": 0xFFFFFFFFFFFFFFF1},
    {"name": "ret", "opcode": 0xFFFFFFFFFFFFFFF2},
    {"name": "ei", "opcode": 0xFFFFFFFFFFFFFFF3},
    {"name": "di", "opcode": 0xFFFFFFFFFFFFFFF4},
    {"name": "iret", "opcode": 0xFFFFFFFFFFFFFFF5},

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
    # Arithmetic
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

    # =========================
    # Logic
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
# ####
#     # =========================
#     # Other ALU ops
#     # =========================

#     {"name": "shl_imm",   "opcode": 0xFFFFFFFFFB3},
#     {"name": "shl_r_imm", "opcode": 0xFFFFFFFB12},

#     {"name": "shr_imm",   "opcode": 0xFFFFFFFFFC3},
#     {"name": "shr_r_imm", "opcode": 0xFFFFFFFC13},

#     # =========================
#     # Jumps
#     # =========================

#     {"name": "jmp_mem",  "opcode": 0xFFFFFF5},
#     {"name": "jz_mem",   "opcode": 0xFFFFFF5},
#     {"name": "jnz_mem",  "opcode": 0xFFFFFF5},
#     {"name": "jc_mem",   "opcode": 0xFFFFFF5},

#     {"name": "jnc_mem",  "opcode": 0xFFFFFF6},
#     {"name": "js_mem",   "opcode": 0xFFFFFF6},
#     {"name": "jns_mem",  "opcode": 0xFFFFFF6},
#     {"name": "jo_mem",   "opcode": 0xFFFFFF6},

#     {"name": "jno_mem",  "opcode": 0xFFFFFF7},
#     {"name": "call_mem", "opcode": 0xFFFFFF7},

#     {"name": "jl_mem",   "opcode": 0xFFFFFF8},
#     {"name": "jg_mem",   "opcode": 0xFFFFFF8},

#     {"name": "jge_mem",  "opcode": 0xFFFFFF9},
#     {"name": "jle_mem",  "opcode": 0xFFFFFF9},

]
