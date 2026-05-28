.data
b_data_0 : 1
b_data_1 : 2
b_data_2 : 3
b_data_3 : 4
b_data_4 : 5
b_data_5 : 6
b_data_6 : 7
b_data_7 : 8
a_data_0 : 1
a_data_1 : 2
a_data_2 : 3
a_data_3 : 4
a_data_4 : 5
a_data_5 : 6
rows_a : 0
rows_b : 0
cols_a : 0
cols_b : 0
a : 0
b : 0
c : 0
temp_0_0 : 0
i : 0
j : 0
k : 0
pluseq_temp_4_0 : 0
temp_6_0 : 0
.text
MOVD R0, 3
MOVD [rows_a], R0
MOVD R0, 2
MOVD [rows_b], R0
MOVD R0, 2
MOVD [cols_a], R0
MOVD R0, 4
MOVD [cols_b], R0
LEA R0, [a_data_0]
MOVD [a], R0
LEA R0, [b_data_0]
MOVD [b], R0
LEA R0, [temp_0_0]
MOVD [c], R0
MOVD R0, 0
MOVD [i], R0
LFOR_START8:
MOVD R0, [i]
MOVD R2, [rows_a]
CMP R0, R2
JL LTRUE1
MOVD R0, 0
JMP LFALSE1
LTRUE1:
MOVD R0, 1
LFALSE1:
CMP R0, 0
JZ LFOR_END8
MOVD R2, 0
MOVD [j], R2
LFOR_START7:
MOVD R2, [j]
MOVD R3, [cols_b]
CMP R2, R3
JL LTRUE2
MOVD R2, 0
JMP LFALSE2
LTRUE2:
MOVD R2, 1
LFALSE2:
CMP R2, 0
JZ LFOR_END7
MOVD R3, 0
MOVD [k], R3
LFOR_START5:
MOVD R3, [k]
MOVD R4, [cols_a]
CMP R3, R4
JL LTRUE3
MOVD R3, 0
JMP LFALSE3
LTRUE3:
MOVD R3, 1
LFALSE3:
CMP R3, 0
JZ LFOR_END5
MOVD R4, [i]
MOVD R6, [a]
MUL R4, 16
ADD R6, R4
MOVD R4, [k]
MUL R4, 8
ADD R6, R4
MOVD R4, [R6]
MOVD R6, [k]
MOVD R7, [b]
MUL R6, 32
ADD R7, R6
MOVD R6, [j]
MUL R6, 8
ADD R7, R6
MOVD R6, [R7]
MUL R4, R6
MOVD [pluseq_temp_4_0], R4
MOVD R4, [i]
MOVD R5, [c]
MUL R4, 32
ADD R5, R4
MOVD R4, [j]
MUL R4, 8
ADD R5, R4
MOVD R6, [R5]
MOVD R7, [pluseq_temp_4_0]
ADD R6, R7
MOVD [R5], R6
MOVD R4, [k]
ADD R4, 1
MOVD [k], R4
JMP LFOR_START5
LFOR_END5:
MOVD R4, [i]
MOVD R5, [c]
MUL R4, 32
ADD R5, R4
MOVD R4, [j]
MUL R4, 8
ADD R5, R4
MOVD R4, [R5]
LEA R5, [temp_6_0]
MOVD [R5], R4
MOVD R10, 0
MOVD R11, R5
MOVD R12, 1
INTR 0
MOVD R3, [j]
ADD R3, 1
MOVD [j], R3
JMP LFOR_START7
LFOR_END7:
MOVD R2, [i]
ADD R2, 1
MOVD [i], R2
JMP LFOR_START8
LFOR_END8:
HLT