INSTRUCTION_SPECS = [

    # =========================
    # Control
    # =========================

    {"name": "nop", "opcode": 0xFFFFFFFFFFFFFFF0},
    {"name": "hlt", "opcode": 0xFFFFFFFFFFFFFFF1},
    {"name": "ret", "opcode": 0xFFFFFFFFFFFFFFF2},
    {"name": "ei",  "opcode": 0xFFFFFFFFFFFFFFF3},
    {"name": "di",  "opcode": 0xFFFFFFFFFFFFFFF4},
    {"name": "iret","opcode": 0xFFFFFFFFFFFFFFF5},

    # =========================
    # MOV
    # =========================

    {"name": "movb_rr",  "opcode": 0xFFFFFFFFFFF100000},
    {"name": "movb_r_imm","opcode": 0xFFFFFFFF00},
    {"name": "movb_r_mem","opcode": 0xFFFF00},
    {"name": "movb_mem_r","opcode": 0xFFFF00},
    {"name": "movb_mem_imm","opcode": 0xF00},

    {"name": "movh_rr",  "opcode": 0xFFFFFFFFFFF01},
    {"name": "movh_r_imm","opcode": 0xFFFFFFFF01},
    {"name": "movh_r_mem","opcode": 0xFFFF01},
    {"name": "movh_mem_r","opcode": 0xFFFF01},
    {"name": "movh_mem_imm","opcode": 0xF01},

    {"name": "movw_rr",  "opcode": 0xFFFFFFFFFFF02},
    {"name": "movw_r_imm","opcode": 0xFFFFFFFF02},
    {"name": "movw_r_mem","opcode": 0xFFFF02},
    {"name": "movw_mem_r","opcode": 0xFFFF02},
    {"name": "movw_mem_imm","opcode": 0xF02},

    {"name": "movd_rr",  "opcode": 0xFFFFFFFFFFF03},
    {"name": "movd_r_imm","opcode": 0xFFFFFFFF03},
    {"name": "movd_r_mem","opcode": 0xFFFF03},
    {"name": "movd_mem_r","opcode": 0xFFFF03},
    {"name": "movd_mem_imm","opcode": 0xF03},

    # =========================
    # LOAD
    # =========================

    {"name": "loadb_mem", "opcode": 0xFFFFFF0},
    {"name": "loadb_imm", "opcode": 0xFFFFFFFFFF0},
    {"name": "loadb_r_mem","opcode": 0xFFFF04},
    {"name": "loadb_r_imm","opcode": 0xFFFFFFFF04},

    {"name": "loadh_mem", "opcode": 0xFFFFFF0},
    {"name": "loadh_imm", "opcode": 0xFFFFFFFFFF0},
    {"name": "loadh_r_mem","opcode": 0xFFFF05},
    {"name": "loadh_r_imm","opcode": 0xFFFFFFFF05},

    {"name": "loadw_mem", "opcode": 0xFFFFFF0},
    {"name": "loadw_imm", "opcode": 0xFFFFFFFFFF0},
    {"name": "loadw_r_mem","opcode": 0xFFFF06},
    {"name": "loadw_r_imm","opcode": 0xFFFFFFFF06},

    {"name": "loadd_mem", "opcode": 0xFFFFFF0},
    {"name": "loadd_imm", "opcode": 0xFFFFFFFFFF0},
    {"name": "loadd_r_mem","opcode": 0xFFFF07},
    {"name": "loadd_r_imm","opcode": 0xFFFFFFFF07},

    # =========================
    # STORE
    # =========================

    {"name": "storeb_mem", "opcode": 0xFFFFFF1},
    {"name": "storeb_r",   "opcode": 0xFFFFFFFFFFFFF0},
    {"name": "storeb_mem_r","opcode": 0xFFFF08},
    {"name": "storeb_mem_imm","opcode": 0xF04},

    {"name": "storeh_mem", "opcode": 0xFFFFFF1},
    {"name": "storeh_r",   "opcode": 0xFFFFFFFFFFFFF0},
    {"name": "storeh_mem_r","opcode": 0xFFFF09},
    {"name": "storeh_mem_imm","opcode": 0xF05},

    {"name": "storew_mem", "opcode": 0xFFFFFF1},
    {"name": "storew_r",   "opcode": 0xFFFFFFFFFFFFF0},
    {"name": "storew_mem_r","opcode": 0xFFFF0A},
    {"name": "storew_mem_imm","opcode": 0xF06},

    {"name": "stored_mem", "opcode": 0xFFFFFF1},
    {"name": "stored_r",   "opcode": 0xFFFFFFFFFFFFF0},
    {"name": "stored_mem_r","opcode": 0xFFFF0B},
    {"name": "stored_mem_imm","opcode": 0xF07},

    # =========================
    # SEXT
    # =========================

    {"name": "sext_r_imm", "opcode": 0xFFFFFFFF08},

    # =========================
    # Arithmetic
    # =========================

    {"name": "add_r_r",   "opcode": 0xFFFFFFFFFF004},
    {"name": "add_r_imm", "opcode": 0xFFFFFFF009},
    {"name": "add_r_mem", "opcode": 0xFFF00C},

    {"name": "sub_r_r",   "opcode": 0xFFFFFFFFFF105},
    {"name": "sub_r_imm", "opcode": 0xFFFFFFF10A},
    {"name": "sub_r_mem", "opcode": 0xFFF10D},

    {"name": "mul_r_r",   "opcode": 0xFFFFFFFFFF306},
    {"name": "mul_r_imm", "opcode": 0xFFFFFFF30B},
    {"name": "mul_r_mem", "opcode": 0xFFF30E},

    {"name": "div_r_r",   "opcode": 0xFFFFFFFFFF407},
    {"name": "div_r_imm", "opcode": 0xFFFFFFF40C},
    {"name": "div_r_mem", "opcode": 0xFFF40F},

    # =========================
    # Logic
    # =========================

    {"name": "and_r_r",   "opcode": 0xFFFFFFFFFF708},
    {"name": "and_r_imm", "opcode": 0xFFFFFFF70D},
    {"name": "and_r_mem", "opcode": 0xFFF710},

    {"name": "or_r_r",    "opcode": 0xFFFFFFFFFF809},
    {"name": "or_r_imm",  "opcode": 0xFFFFFFF80E},
    {"name": "or_r_mem",  "opcode": 0xFFF811},

    {"name": "xor_r_r",   "opcode": 0xFFFFFFFFFF90A},
    {"name": "xor_r_imm", "opcode": 0xFFFFFFF90F},
    {"name": "xor_r_mem", "opcode": 0xFFF912},

    # =========================
    # Shifts
    # =========================

    {"name": "shl_imm",   "opcode": 0xFFFFFFFFFB3},
    {"name": "shl_r_imm", "opcode": 0xFFFFFFFB12},

    {"name": "shr_imm",   "opcode": 0xFFFFFFFFFC3},
    {"name": "shr_r_imm", "opcode": 0xFFFFFFFC13},

    # =========================
    # Jumps
    # =========================

    {"name": "jmp_mem",  "opcode": 0xFFFFFF5},
    {"name": "jz_mem",   "opcode": 0xFFFFFF5},
    {"name": "jnz_mem",  "opcode": 0xFFFFFF5},
    {"name": "jc_mem",   "opcode": 0xFFFFFF5},

    {"name": "jnc_mem",  "opcode": 0xFFFFFF6},
    {"name": "js_mem",   "opcode": 0xFFFFFF6},
    {"name": "jns_mem",  "opcode": 0xFFFFFF6},
    {"name": "jo_mem",   "opcode": 0xFFFFFF6},

    {"name": "jno_mem",  "opcode": 0xFFFFFF7},
    {"name": "call_mem", "opcode": 0xFFFFFF7},

    {"name": "jl_mem",   "opcode": 0xFFFFFF8},
    {"name": "jg_mem",   "opcode": 0xFFFFFF8},

    {"name": "jge_mem",  "opcode": 0xFFFFFF9},
    {"name": "jle_mem",  "opcode": 0xFFFFFF9},

]
