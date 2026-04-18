.import "math.lib"
.extern MATRIX_GET_LINEAR
.extern MATRIX_SET_LINEAR

.data
    matrix_a_base: 1028
    matrix_b_base: 1076
    matrix_c_base: 20455
    rows_a: 3
    rows_b: 2
    cols_a: 2
    cols_b: 4
    temp: 0

.text
    # cargar bases
    MOVH R10, [matrix_a_base]
    MOVH R11, [matrix_b_base]
    MOVH R12, [matrix_c_base]

    # INIT MATRIZ A
    MOVD R6, 0        # i
    MOVD R7, 1        # valor inicial

INIT_A_I:
    MOVD R9, 0        # j

INIT_A_J:
    MOVD R0, R10
    MOVD R1, [cols_a]
    MOVD R2, R6
    MOVD R3, R9
    MOVD R4, R7

    CALL MATRIX_SET_LINEAR

    INC R7            # value++

    INC R9
    CMP R9, [cols_a]
    JL INIT_A_J

    INC R6
    CMP R6, [rows_a]
    JL INIT_A_I


    # INIT MATRIZ B
    MOVD R6, 0        # i
    MOVD R7, 1        # valor inicial

INIT_B_I:
    MOVD R9, 0        # j

INIT_B_J:
    MOVD R0, R11
    MOVD R1, [cols_b]
    MOVD R2, R6
    MOVD R3, R9
    MOVD R4, R7

    CALL MATRIX_SET_LINEAR

    INC R7            # value++

    INC R9
    CMP R9, [cols_b]
    JL INIT_B_J

    INC R6
    CMP R6, [rows_b]
    JL INIT_B_I


    # i = 0
    MOVD R6, 0

LOOP_I:
    MOVD R7, 0        # j

LOOP_J:
    MOVD R8, 0        # suma
    MOVD R9, 0        # k

LOOP_K:
    # A[i][k]
    MOVD R0, R10
    MOVD R1, [cols_a]
    MOVD R2, R6
    MOVD R3, R9

    CALL MATRIX_GET_LINEAR
    MOVD R4, R5        # A

    PUSH R4

    # B[k][j]
    MOVD R0, R11
    MOVD R1, [cols_b]
    MOVD R2, R9
    MOVD R3, R7

    CALL MATRIX_GET_LINEAR
    # B en R5

    POP R4

    # suma += A * B
    MUL R4, R5
    ADD R8, R4

    INC R9
    CMP R9, [cols_a]
    JL LOOP_K

    # C[i][j]
    MOVD R0, R12
    MOVD R1, [cols_b]
    MOVD R2, R6
    MOVD R3, R7
    MOVD R4, R8

    CALL MATRIX_SET_LINEAR

    INC R7
    CMP R7, [cols_b]
    JL LOOP_J

    INC R6
    CMP R6, [rows_a]
    JL LOOP_I

    # print init
    MOVH R0, [rows_a]
    MUL R0, [cols_b]
    MUL R0, 8
    MOVD R6, 0        # i
    MOVD R11, 0

PRINT_C_I:
    MOVD R7, [matrix_c_base]
    ADD R7, R6
    MOVD R2, [R7]

    MOVD [temp], R2
    MOVD R10, 0
    LEA R11, [temp]
    MOVD R12, 1
    INTR 0

    ADD R6, 8
    CMP R0, R6
    JG PRINT_C_I

    HLT