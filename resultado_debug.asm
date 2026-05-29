.data
alumnos_data_0 : 0
alumnos_data_1 : 0
alumnos_data_2 : 0
alumnos_data_3 : 0
n : 0
temp_0_0 : 0
temp_0_1 : 0
temp_1_0 : 0
temp_1_1 : 0
temp_2_0 : 0
temp_2_1 : 0
temp_3_0 : 0
temp_3_1 : 0
alumnos : 0
al_codigo : 0
al_nota : 0
i : 0
temp_4_0 : 0
temp_6_0 : 0
temp_7_0 : 0
.text
MOVD R0, 4
MOVD [n], R0
LEA R0, [temp_0_0]
MOVD R2, 101
MOVD R3, R0
MOVD [R3], R2
MOVD R2, 85
MOVD R3, R0
ADD R3, 8
MOVD [R3], R2
LEA R5, [alumnos_data_0]
MOVD [R5], R0
LEA R2, [temp_1_0]
MOVD R3, 102
MOVD R4, R2
MOVD [R4], R3
MOVD R3, 72
MOVD R4, R2
ADD R4, 8
MOVD [R4], R3
LEA R5, [alumnos_data_1]
MOVD [R5], R2
LEA R3, [temp_2_0]
MOVD R4, 103
MOVD R5, R3
MOVD [R5], R4
MOVD R4, 91
MOVD R5, R3
ADD R5, 8
MOVD [R5], R4
LEA R5, [alumnos_data_2]
MOVD [R5], R3
LEA R4, [temp_3_0]
MOVD R5, 104
MOVD R6, R4
MOVD [R6], R5
MOVD R5, 68
MOVD R6, R4
ADD R6, 8
MOVD [R6], R5
LEA R5, [alumnos_data_3]
MOVD [R5], R4
LEA R5, [alumnos_data_0]
MOVD [alumnos], R5
MOVD R5, 0
MOVD [i], R5
LFOR_START8:
MOVD R5, [n]
LEA R7, [temp_4_0]
MOVD [R7], R5
MOVD R6, [i]
LEA R8, [temp_4_0]
MOVD R7, [R8]
CMP R6, R7
JL LTRUE5
MOVD R6, 0
JMP LFALSE5
LTRUE5:
MOVD R6, 1
LFALSE5:
CMP R6, 0
JZ LFOR_END8
MOVD R5, [R7]
MOVD [al_codigo], R5
MOVD R10, R8
ADD R10, 8
MOVD R5, [R10]
MOVD [al_nota], R5
MOVD R5, [al_codigo]
LEA R10, [temp_6_0]
MOVD [R10], R5
MOVD R10, 0
MOVD R11, R10
MOVD R12, 1
INTR 0
MOVD R5, [al_nota]
LEA R10, [temp_7_0]
MOVD [R10], R5
MOVD R10, 0
MOVD R11, R10
MOVD R12, 1
INTR 0
MOVD R5, [i]
ADD R5, 1
MOVD [i], R5
JMP LFOR_START8
LFOR_END8:
HLT