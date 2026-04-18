import struct
from .asm_lexer import AsmLexer
import ply.yacc as yacc
from isa.microinstructions import MICROINSTRUCTION_SPECS

class AsmParser:
    lexer_obj = AsmLexer()
    lexer = lexer_obj.build()
    tokens= lexer_obj.tokens

    def __init__(self):
        self.symbol_table = {}  # etiqueta -> dirección
        self.var_table = {}  # variable -> dirección
        self.program_data      = []  # lista de instrucciones
        self.program_text      = []  # lista de instrucciones
        self.program           = []
        self.pending      = []
        self.sect         = None

# ─── PARSER ──────────────────────────────────────────────

    def p_program(self, p):
        '''program : line
                | program line'''

    def p_line_label(self, p):
        'line : LABEL COLON NEWLINE'
        # Registrar la etiqueta con la dirección actual
        if self.sect == '.text':
            cur_program = self.program_text
            self.symbol_table[p[1]] = str(len(cur_program))

    def p_line_variable_float(self, p):
        'line : VAR COLON FLOAT NEWLINE'
        self.var_table[p[1]] = len(self.program_data)
        self.program_data.append(p[1])
        number = bytearray(struct.pack('<d', p[3])).hex()
        p[0] = number
        self.program.append(p[0])

    def p_line_variable_number(self, p):
        'line : VAR COLON NUMBER NEWLINE'
        self.var_table[p[1]] = len(self.program_data)
        self.program_data.append(p[1])
        p[0] = p[3].to_bytes(8, byteorder='little').hex()
        self.program.append(str(p[0]))

    def p_line_section(self, p):
        'line : SECTION'
        self.sect = p[1].lower()
        self.program.append(str(p[1]))

    def p_line_import(self, p):
        '''line : SECTION REFERENCE
                | SECTION VAR'''
                
        self.sect = p[1].lower()
        self.program.append(f"{str(p[1])} {p[2]}")

    def p_line_instr(self, p):
        '''line : instruction NEWLINE
                | instruction'''
        self.program_text.append(p[1])
        self.program.append(p[1])

    def p_line_empty(self, p):
            'line : NEWLINE'

    def p_instr_reg_reg(self, p):
        'instruction : MNEMONIC REGISTER COMMA REGISTER'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_rr':
                code = str(hex(p[2]))[2:] + str(hex(p[4]))[2:] + str(instruction["opcode"].to_bytes(7, byteorder='little').hex())
                p[0] = code

    def p_instr_reg_imm(self, p):
        'instruction : MNEMONIC REGISTER COMMA NUMBER'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_ri':
                code =  str(instruction["opcode"].to_bytes(6, byteorder='big').hex())[1:] + str(hex(p[2]))[2:]
                n = len(code)
                code = str(p[4].to_bytes(2, byteorder='little').hex()) + "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                p[0] = code
    
    def p_instr_reg_mem(self, p):
        'instruction : MNEMONIC REGISTER COMMA MEMORY'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_rm':
                code =  str(instruction["opcode"].to_bytes(4, byteorder='big').hex())[1:] + str(hex(p[2]))[2:]
                n = len(code)
                code = str(p[4].to_bytes(4, byteorder='little').hex()) + "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                p[0] = code
    
    def p_instr_reg_var(self, p):
        'instruction : MNEMONIC REGISTER COMMA LBRACKET VAR RBRACKET'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_rm':
                code =  str(instruction["opcode"].to_bytes(4, byteorder='big').hex())[1:] + str(hex(p[2]))[2:]
                n = len(code)
                code = '[' + f'{self.var_table[p[5]]}' + ']' + "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                p[0] = code

    def p_instr_reg_ind(self, p):
        'instruction : MNEMONIC REGISTER COMMA LBRACKET REGISTER RBRACKET'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_rn':
                code = str(hex(p[2]))[2:] + str(hex(p[5]))[2:] + str(instruction["opcode"].to_bytes(7, byteorder='little').hex())
                p[0] = code

    def p_instr_mem_reg(self, p):
        'instruction : MNEMONIC MEMORY COMMA REGISTER'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_mr':
                code =  str(instruction["opcode"].to_bytes(4, byteorder='big').hex())[1:] + str(p[2].to_bytes(4, byteorder= 'big').hex()) + str(hex(p[4]))[2:]
                n = len(code)
                code =  "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                p[0] = code
    
    def p_instr_var_reg(self, p):
        'instruction : MNEMONIC LBRACKET VAR RBRACKET COMMA REGISTER'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_mr':
                code =  str(instruction["opcode"].to_bytes(4, byteorder='big').hex())[1:] + '-'
                n = len(code)
                code =  "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                code = str(hex(p[6]))[2:] + '[' + f'{self.var_table[p[3]]}' + ']' + code

                p[0] = code

    def p_instr_mem_inm(self, p):
        'instruction : MNEMONIC MEMORY COMMA NUMBER'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_mi':
                code =  str(instruction["opcode"].to_bytes(2, byteorder='big').hex()) + str(p[2].to_bytes(4, byteorder= 'big').hex()) + str(p[4].to_bytes(2, byteorder='big').hex())
                n = len(code)
                code =  "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                p[0] = code

    def p_instr_var_inm(self, p):
        'instruction : MNEMONIC LBRACKET VAR RBRACKET COMMA NUMBER'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_mi':
                code =  str(instruction["opcode"].to_bytes(2, byteorder='big').hex())
                n = len(code)
                code =  "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                code = '[' + f'{self.var_table[p[3]]}' + ']' + code
                code = str(p[6].to_bytes(2, byteorder='little').hex()) + code
                p[0] = code

    def p_instr_ind_reg(self, p):
        'instruction : MNEMONIC LBRACKET REGISTER RBRACKET COMMA REGISTER'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_nr':
                code =  str(instruction["opcode"].to_bytes(7, byteorder='big').hex()) + str(hex(p[3]))[2:] + str(hex(p[6]))[2:]
                n = len(code)
                code =  "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                p[0] = code

    def p_instr_mem(self, p):
        'instruction : MNEMONIC MEMORY'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_m':
                code =  str(instruction["opcode"].to_bytes(4, byteorder='big').hex())
                n = len(code)
                code = str(p[2].to_bytes(4, byteorder='little').hex()) + "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                p[0] = code

    def p_instr_reg(self, p):
        'instruction : MNEMONIC REGISTER'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_r':
                code =  str(instruction["opcode"].to_bytes(8, byteorder='big').hex())[1:] + str(p[2])
                n = len(code)
                code = "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                p[0] = code

    def p_instr_inm(self, p):
        'instruction : MNEMONIC NUMBER'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_i' or instruction["name"]=='int_i':
                code =  str(instruction["opcode"].to_bytes(6, byteorder='big').hex())
                n = len(code)
                code = str(p[2].to_bytes(2, byteorder='little').hex()) + "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                p[0] = code

    def p_instr_label(self, p):
        '''instruction : MNEMONIC LABEL
                        | MNEMONIC VAR'''
        
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]+'_m':
                code =  str(instruction["opcode"].to_bytes(4, byteorder='big').hex())
                n = len(code)
                try:
                    code = '{' + f'{self.symbol_table[p[2]]}'+ '}' + "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                    
                except KeyError:
                    code = "".join([code[n-i-2] + code[n-i-1] for i in range(len(code)) if i%2 == 0])
                    self.pending.append((p[2], len(self.program)))
                finally:
                    p[0] = code

    def p_instr_single(self, p):
        'instruction : MNEMONIC'
        for instruction in MICROINSTRUCTION_SPECS:
            if instruction["name"] == p[1]:
                code =  str(instruction["opcode"].to_bytes(8, byteorder='little').hex())
                p[0] = code

    def p_error(self, p):
        if p:
            print(f"Error sintáctico en línea {len(self.program)}: '{p.value}'")
    
    def get_parser(self):
        self.parser = yacc.yacc(module=self)
        return self.parser

    def parse(self, codigo_asm):
        parser = self.get_parser()
        parser.parse(codigo_asm, lexer=self.lexer)
