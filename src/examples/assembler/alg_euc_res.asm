.data
    a: 987654
    b: 123456
    temp: 0
.text
    MOVD R0, [a]
    MOVD R1, [b]

    LOOP:
        CMP R0, R1
        JZ FIN
        JG GREATER
        SUB R1, R0
        JMP LOOP
    
    GREATER:
        SUB R0, R1
        JMP LOOP

    FIN:
        MOVW [temp], R1
        MOVH R10, 0
        LEA R11, [temp]
        MOVW R12, 1
        INTR 0
        HLT
