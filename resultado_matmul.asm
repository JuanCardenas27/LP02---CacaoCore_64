.data
c_data_0 : 0
c_data_1 : 0
c_data_2 : 0
c_data_3 : 0
c_data_4 : 0
c_data_5 : 0
c_data_6 : 0
c_data_7 : 0
c_data_8 : 0
c_data_9 : 0
c_data_10 : 0
c_data_11 : 0
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
i : 0
temp_0_0 : 0
j : 0
temp_2_0 : 0
k : 0
temp_4_0 : 0
pluseq_temp_6_0 : 0
temp_8_0 : 0
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
LEA R0, [c_data_0]
MOVD [c], R0
MOVD R0, 0
MOVD [i], R0
LFOR_START10:
MOVD R0, [rows_a]
LEA R3, [temp_0_0]
MOVD [R3], R0
MOVD R2, [i]
LEA R4, [temp_0_0]
MOVD R3, [R4]
CMP R2, R3
JL LTRUE1
MOVD R2, 0
JMP LFALSE1
LTRUE1:
MOVD R2, 1
LFALSE1:
CMP R2, 0
JZ LFOR_END10
MOVD R0, 0
MOVD [j], R0
LFOR_START9:
MOVD R0, [cols_b]
LEA R4, [temp_2_0]
MOVD [R4], R0
MOVD R3, [j]
LEA R5, [temp_2_0]
MOVD R4, [R5]
CMP R3, R4
JL LTRUE3
MOVD R3, 0
JMP LFALSE3
LTRUE3:
MOVD R3, 1
LFALSE3:
CMP R3, 0
JZ LFOR_END9
MOVD R0, 0
MOVD [k], R0
LFOR_START7:
MOVD R0, [cols_a]
LEA R5, [temp_4_0]
MOVD [R5], R0
MOVD R4, [k]
LEA R6, [temp_4_0]
MOVD R5, [R6]
CMP R4, R5
JL LTRUE5
MOVD R4, 0
JMP LFALSE5
LTRUE5:
MOVD R4, 1
LFALSE5:
CMP R4, 0
JZ LFOR_END7
MOVD R0, [i]
MOVD R6, [a]
MUL R0, 16
ADD R6, R0
MOVD R0, [k]
MUL R0, 8
ADD R6, R0
MOVD R0, [R6]
MOVD R6, [k]
MOVD R7, [b]
MUL R6, 32
ADD R7, R6
MOVD R6, [j]
MUL R6, 8
ADD R7, R6
MOVD R6, [R7]
MUL R0, R6
MOVD [pluseq_temp_6_0], R0
MOVD R0, [i]
MOVD R5, [c]
MUL R0, 32
ADD R5, R0
MOVD R0, [j]
MUL R0, 8
ADD R5, R0
MOVD R6, [R5]
MOVD R7, [pluseq_temp_6_0]
ADD R6, R7
MOVD [R5], R6
MOVD R0, [k]
ADD R0, 1
MOVD [k], R0
JMP LFOR_START7
LFOR_END7:
MOVD R0, [i]
MOVD R5, [c]
MUL R0, 32
ADD R5, R0
MOVD R0, [j]
MUL R0, 8
ADD R5, R0
MOVD R0, [R5]
LEA R5, [temp_8_0]
MOVD [R5], R0
MOVD R10, 0
MOVD R11, R5
MOVD R12, 1
INTR 0
MOVD R0, [j]
ADD R0, 1
MOVD [j], R0
JMP LFOR_START9
LFOR_END9:
MOVD R0, [i]
ADD R0, 1
MOVD [i], R0
JMP LFOR_START10
LFOR_END10:
HLT