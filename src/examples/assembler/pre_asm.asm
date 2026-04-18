.data
    pi:    3.14159
    e:     52
    cero:  0
.text
    INICIO:
        ;coment
        jmp FIN
        MOVH R1, 10
        MOVH R1, [cero]
        MOVH [cero], R1
        MOVH 0x00040000, R1
        MOVH R4, [R9]
        ADD R0, R10
        JZ FIN
        movb R2, R0
    FIN:
        hlt