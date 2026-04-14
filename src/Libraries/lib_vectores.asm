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
;   vec_init
;   vec_set
;   vec_get
;   vec_len
;   vec_sum
;   vec_max
;   vec_min
;   vec_copy
;   vec_swap_elem
;   matrix_get_linear
;   matrix_set_linear
;   matrix_sum_row
;   matrix_find_max
;   matrix_sum_all

.text

; @func vec_init
; vec_init(r0=base, r1=len)
vec_init:
    movd r4, r0
    movd r3, 0
    movd r2, 0
loop_init:
    cmp r2, r1
    jge end_init
    movd [r4], r3
    add r4, 8
    add r2, 1
    jmp loop_init
end_init:
    ret
; @endfunc

; @func vec_set
; vec_set(r0=base, r2=index, r3=valor)
vec_set:
    movd r4, r2
    mul r4, 8
    add r4, r0
    movd [r4], r3
    ret
; @endfunc

; @func vec_get
; vec_get(r0=base, r2=index) -> r5=valor
vec_get:
    movd r4, r2
    mul r4, 8
    add r4, r0
    movd r5, [r4]
    ret
; @endfunc

; @func vec_len
; vec_len(r1=len) -> r5=len
vec_len:
    movd r5, r1
    ret
; @endfunc

; @func vec_sum
; vec_sum(r0=base, r1=len) -> r5=suma
vec_sum:
    movd r5, 0
    movd r2, 0
    movd r4, r0
loop_sum:
    cmp r2, r1
    jge end_sum
    movd r3, [r4]
    add r5, r3
    add r4, 8
    add r2, 1
    jmp loop_sum
end_sum:
    ret
; @endfunc

; @func vec_max
; vec_max(r0=base, r1=len) -> r5=maximo
vec_max:
    movd r5, [r0]
    movd r2, 1
    movd r4, r0
    add r4, 8
loop_max:
    cmp r2, r1
    jge end_max
    movd r3, [r4]
    cmp r3, r5
    jle no_update_max
    movd r5, r3
no_update_max:
    add r4, 8
    add r2, 1
    jmp loop_max
end_max:
    ret
; @endfunc

; @func vec_min
; vec_min(r0=base, r1=len) -> r5=minimo
vec_min:
    movd r5, [r0]
    movd r2, 1
    movd r4, r0
    add r4, 8
loop_min:
    cmp r2, r1
    jge end_min
    movd r3, [r4]
    cmp r3, r5
    jge no_update_min
    movd r5, r3
no_update_min:
    add r4, 8
    add r2, 1
    jmp loop_min
end_min:
    ret
; @endfunc

; @func vec_copy
; vec_copy(r0=src_base, r1=len, r6=dst_base)
vec_copy:
    movd r4, r0
    movd r7, r6
    movd r2, 0
loop_copy:
    cmp r2, r1
    jge end_copy
    movd r3, [r4]
    movd [r7], r3
    add r4, 8
    add r7, 8
    add r2, 1
    jmp loop_copy
end_copy:
    ret
; @endfunc

; @func vec_swap_elem
; vec_swap_elem(r0=base, r2=i, r3=j)
vec_swap_elem:
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

; @func matrix_get_linear
; matrix_get_linear(r0=base, r1=cols, r2=row, r3=col) -> r5=valor
matrix_get_linear:
    movd r4, r2
    mul r4, r1
    add r4, r3
    mul r4, 8
    add r4, r0
    movd r5, [r4]
    ret
; @endfunc

; @func matrix_set_linear
; matrix_set_linear(r0=base, r1=cols, r2=row, r3=col, r4=value)
matrix_set_linear:
    movd r8, r2
    mul r8, r1
    add r8, r3
    mul r8, 8
    add r8, r0
    movd [r8], r4
    ret
; @endfunc

; @func matrix_sum_row
; matrix_sum_row(r0=base, r1=cols, r2=row) -> r5=suma
matrix_sum_row:
    movd r4, r2
    mul r4, r1
    mul r4, 8
    add r4, r0
    movd r5, 0
    movd r2, 0
loop_sum_row:
    cmp r2, r1
    jge end_sum_row
    movd r3, [r4]
    add r5, r3
    add r4, 8
    add r2, 1
    jmp loop_sum_row
end_sum_row:
    ret
; @endfunc

; @func matrix_find_max
; matrix_find_max(r0=base, r1=total_elements) -> r5=maximo
matrix_find_max:
    movd r5, [r0]
    movd r2, 1
    movd r4, r0
    add r4, 8
loop_find_max:
    cmp r2, r1
    jge end_find_max
    movd r3, [r4]
    cmp r3, r5
    jle no_update_max2
    movd r5, r3
no_update_max2:
    add r4, 8
    add r2, 1
    jmp loop_find_max
end_find_max:
    ret
; @endfunc

; @func matrix_sum_all
; matrix_sum_all(r0=base, r1=total_elements) -> r5=suma
matrix_sum_all:
    movd r5, 0
    movd r2, 0
    movd r4, r0
loop_sum_all:
    cmp r2, r1
    jge end_sum_all
    movd r3, [r4]
    add r5, r3
    add r4, 8
    add r2, 1
    jmp loop_sum_all
end_sum_all:
    ret
; @endfunc
