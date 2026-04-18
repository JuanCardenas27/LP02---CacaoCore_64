.import "math.lib"
.extern MATRIX_GET_LINEAR
.extern MATRIX_SET_LINEAR

.data
    matrix_a_base: 1028
    matrix_b_base: 1076
    matrix_c_base: 20455
    cols_a: 2
    cols_b: 4
    cols_c: 4
    result: 0

.text
    # Multiplicación de matrices: A(3x2) * B(2x4) = C(3x4)
    # Usa funciones de lib_vectores para acceso a matrices

    # Cargar base de matriz A directamente
    MOVH R9, 1028

    # Cargar base de matriz B directamente
    MOVH R10, 1076

    # Cargar base de matriz C directamente
    MOVH R11, 2455

    # i = 0 (contador de filas)
    MOVH R3, 0

    # --- LOOP_I (filas: 0 a 2) ---
LOOP_I:
    # j = 0 (contador de columnas)
    MOVH R4, 0

    # --- LOOP_J (columnas: 0 a 3) ---
LOOP_J:
    # suma = 0 (acumulador)
    MOVH R8, 0

    # k = 0 (contador de sumatoria)
    MOVH R5, 0

    # --- LOOP_K (sumatoria: 0 a 1) ---
LOOP_K:
    # Leer A[i][k] usando matrix_get_linear
    # Preparar parámetros
    MOVD R0, R9        # r0 = base A
    LEA R1, [cols_a]
    MOVH R1, [R1]      # r1 = cols de A = 2
    MOVD R2, R3        # r2 = row = i
    MOVD R3, R5        # r3 = col = k

    # Llamar a matrix_get_linear
    CALL MATRIX_GET_LINEAR
    MOVD R6, R5        # r6 = A[i][k] (resultado en r5)

    # Leer B[k][j] usando matrix_get_linear
    # Preparar parámetros
    MOVD R0, R10       # r0 = base B
    LEA R1, [cols_b]
    MOVH R1, [R1]      # r1 = cols de B = 4
    MOVD R2, R5        # r2 = row = k
    MOVD R3, R4        # r3 = col = j

    # Llamar a matrix_get_linear
    CALL MATRIX_GET_LINEAR
    MOVD R7, R5        # r7 = B[k][j] (resultado en r5)

    # Multiplicar A[i][k] * B[k][j]
    MUL R6, R7

    # Acumular suma += r6
    ADD R8, R6

    # k++
    INC R5

    # if (k < 2) goto LOOP_K
    CMP R5, 2
    JL LOOP_K

    # --- Guardar resultado en C[i][j] usando matrix_set_linear ---
    # Preparar parámetros
    MOVD R0, R11       # r0 = base C
    LEA R1, [cols_c]
    MOVH R1, [R1]      # r1 = cols de C = 4
    MOVD R2, R3        # r2 = row = i
    MOVD R3, R4        # r3 = col = j
    MOVD R4, R8        # r4 = value = suma

    # Llamar a matrix_set_linear
    CALL MATRIX_SET_LINEAR

    # j++
    INC R4

    # if (j < 4) goto LOOP_J
    CMP R4, 4
    JL LOOP_J

    # i++
    INC R3

    # if (i < 3) goto LOOP_I
    CMP R3, 3
    JL LOOP_I

    # --- FIN DEL PROGRAMA ---
    MOVH R0, 0
    LEA R3, [result]
    MOVW R12, 1
    INTR 0
    HLT