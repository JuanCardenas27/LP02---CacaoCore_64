; lib_vectores.asm - Libreria de Vectores (Listas)
; Cacao Core 64 - Tarea 29
;
; Convencion de registros:
;   r0  = direccion base del vector
;   r1  = longitud del vector (numero de elementos)
;   r2  = indice / argumento general
;   r3  = valor a escribir / resultado temporal
;   r4  = direccion calculada (base + indice*8)
;   r5  = valor de retorno / resultado
;   r13 = SP (stack pointer)
;   r14 = LR (link register / direccion de retorno)
;   r15 = ACC (acumulador)
;
; Subrutinas:
;   VEC_INIT
;   VEC_SET
;   VEC_GET
;   VEC_LEN
;   VEC_SUM
;   VEC_MAX
;   VEC_MIN
;   VEC_COPY
;   VEC_SWAP_ELEM
;   MATRIX_GET_LINEAR
;   MATRIX_SET_LINEAR
;   MATRIX_SUM_ROW
;   MATRIX_FIND_MAX
;   MATRIX_SUM_ALL

.text

; @func VEC_INIT
; VEC_INIT(r0=base, r1=len)
VEC_INIT:
    movd r4, r0
    movd r3, 0
    movd r2, 0
LOOP_INIT:
    cmp r2, r1
    jge END_INIT
    movd [r4], r3
    add r4, 8
    add r2, 1
    jmp LOOP_INIT
END_INIT:
    ret
; @endfunc

; @func VEC_SET
; VEC_SET(r0=base, r2=index, r3=valor)
VEC_SET:
    movd r4, r2
    mul r4, 8
    add r4, r0
    movd [r4], r3
    ret
; @endfunc

; @func VEC_GET
; VEC_GET(r0=base, r2=index) -> r5=valor
VEC_GET:
    movd r4, r2
    mul r4, 8
    add r4, r0
    movd r5, [r4]
    ret
; @endfunc

; @func VEC_LEN
; VEC_LEN(r1=len) -> r5=len
VEC_LEN:
    movd r5, r1
    ret
; @endfunc

; @func VEC_SUM
; VEC_SUM(r0=base, r1=len) -> r5=suma
VEC_SUM:
    movd r5, 0
    movd r2, 0
    movd r4, r0
LOOP_SUM:
    cmp r2, r1
    jge END_SUM
    movd r3, [r4]
    add r5, r3
    add r4, 8
    add r2, 1
    jmp LOOP_SUM
END_SUM:
    ret
; @endfunc

; @func VEC_MAX
; VEC_MAX(r0=base, r1=len) -> r5=maximo
VEC_MAX:
    movd r5, [r0]
    movd r2, 1
    movd r4, r0
    add r4, 8
LOOP_MAX:
    cmp r2, r1
    jge END_MAX
    movd r3, [r4]
    cmp r3, r5
    jle NO_UPDATE_MAX
    movd r5, r3
NO_UPDATE_MAX:
    add r4, 8
    add r2, 1
    jmp LOOP_MAX
END_MAX:
    ret
; @endfunc

; @func VEC_MIN
; VEC_MIN(r0=base, r1=len) -> r5=minimo
VEC_MIN:
    movd r5, [r0]
    movd r2, 1
    movd r4, r0
    add r4, 8
LOOP_MIN:
    cmp r2, r1
    jge END_MIN
    movd r3, [r4]
    cmp r3, r5
    jge NO_UPDATE_MIN
    movd r5, r3
NO_UPDATE_MIN:
    add r4, 8
    add r2, 1
    jmp LOOP_MIN
END_MIN:
    ret
; @endfunc

; @func VEC_COPY
; VEC_COPY(r0=src_base, r1=len, r6=dst_base)
VEC_COPY:
    movd r4, r0
    movd r7, r6
    movd r2, 0
LOOP_COPY:
    cmp r2, r1
    jge END_COPY
    movd r3, [r4]
    movd [r7], r3
    add r4, 8
    add r7, 8
    add r2, 1
    jmp LOOP_COPY
END_COPY:
    ret
; @endfunc

; @func VEC_SWAP_ELEM
; VEC_SWAP_ELEM(r0=base, r2=i, r3=j)
VEC_SWAP_ELEM:
    movd r4, r2
    mul r4, 8
    add r4, r0
    movd r8, r3
    mul r8, 8
    add r8, r0
    movd r9, [r4]
    movd r10, [r8]
    movd [r4], r10
    movd [r8], r9
    ret
; @endfunc

; @func MATRIX_GET_LINEAR
; MATRIX_GET_LINEAR(r0=base, r1=cols, r2=row, r3=col) -> r5=valor
MATRIX_GET_LINEAR:
    movd r4, r2
    mul r4, r1
    add r4, r3
    mul r4, 8
    add r4, r0
    movd r5, [r4]
    ret
; @endfunc

; @func MATRIX_SET_LINEAR
; MATRIX_SET_LINEAR(r0=base, r1=cols, r2=row, r3=col, r4=value)
MATRIX_SET_LINEAR:
    movd r8, r2
    mul r8, r1
    add r8, r3
    mul r8, 8
    add r8, r0
    movd [r8], r4
    ret
; @endfunc

; @func MATRIX_SUM_ROW
; MATRIX_SUM_ROW(r0=base, r1=cols, r2=row) -> r5=suma
MATRIX_SUM_ROW:
    movd r4, r2
    mul r4, r1
    mul r4, 8
    add r4, r0
    movd r5, 0
    movd r2, 0
LOOP_SUM_ROW:
    cmp r2, r1
    jge END_SUM_ROW
    movd r3, [r4]
    add r5, r3
    add r4, 8
    add r2, 1
    jmp LOOP_SUM_ROW
END_SUM_ROW:
    ret
; @endfunc

; @func MATRIX_FIND_MAX
; MATRIX_FIND_MAX(r0=base, r1=total_elements) -> r5=maximo
MATRIX_FIND_MAX:
    movd r5, [r0]
    movd r2, 1
    movd r4, r0
    add r4, 8
LOOP_FIND_MAX:
    cmp r2, r1
    jge END_FIND_MAX
    movd r3, [r4]
    cmp r3, r5
    jle NO_UPDATE_MAX2
    movd r5, r3
NO_UPDATE_MAX2:
    add r4, 8
    add r2, 1
    jmp LOOP_FIND_MAX
END_FIND_MAX:
    ret
; @endfunc

; @func MATRIX_SUM_ALL
; MATRIX_SUM_ALL(r0=base, r1=total_elements) -> r5=suma
MATRIX_SUM_ALL:
    movd r5, 0
    movd r2, 0
    movd r4, r0
LOOP_SUM_ALL:
    cmp r2, r1
    jge END_SUM_ALL
    movd r3, [r4]
    add r5, r3
    add r4, 8
    add r2, 1
    jmp LOOP_SUM_ALL
END_SUM_ALL:
    ret
; @endfunc
