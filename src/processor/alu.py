class ALU:
    def __init__(self, acumulator, flags):
        self.acm = acumulator
        self.flags = flags 

    def _check_flags(self, result):
        if result >= 2**63 or result < -2**63:
            self.flags[0] += 2 #Encendemos el bit 2 overflow
            result = int.from_bytes(result.to_bytes(9, byteorder='little', signed=True)[0:8], byteorder="little", signed=True)

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative
        
        return result

    def _reset_flags(self, positions = (1,2,3,4)):
        for i in positions:
            self.flags[0] &= ~(1 << i)

    def add(self, op1:bytearray, op2:bytearray):

        #Resetea las banderas que se pueden modificar
        
        self._reset_flags()

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 + num2

        result = self._check_flags(result)

        num1 = int.from_bytes(op1, byteorder="little", signed=False) 
        num2 = int.from_bytes(op2, byteorder="little", signed=False)

        uns_result = num1 + num2
        if uns_result > 2**64:
            self.flags[0] += 4 #Encendemos el bit 3 carry

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)

    def sub(self, op1:bytearray, op2:bytearray):
        
        #Resetea las banderas que se pueden modificar
        
        self._reset_flags()

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 - num2

        result = self._check_flags(result)

        num1 = int.from_bytes(op1, byteorder="little", signed=False) 
        num2 = int.from_bytes(op2, byteorder="little", signed=False)

        uns_result = num1 - num2
        if uns_result > 2**64:
            self.flags[0] += 4 #Encendemos el bit 3 carry

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)

    def inc(self, op1:bytearray):
        #Resetea las banderas que se pueden modificar
        self.add(op1, (1).to_bytes(8, byteorder='little', signed=True))
    
    def mul(self, op1:bytearray, op2:bytearray):
        #Resetea las banderas que se pueden modificar
        
        self._reset_flags()

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 * num2

        result = self._check_flags(result)

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)
    
    def div(self, op1:bytearray, op2:bytearray):
        #Resetea las banderas que se pueden modificar
        self._reset_flags()

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 // num2

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)

        return num1%num2
    
    def dec(self, op1:bytearray):
        #Resetea las banderas que se pueden modificar
        self.sub(op1, (1).to_bytes(8, byteorder='little', signed=True))

    def cmp(self, op1:bytearray, op2:bytearray):
        #Resetea las banderas que se pueden modificar
        self._reset_flags()

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 - num2

        result = self._check_flags(result)

        num1 = int.from_bytes(op1, byteorder="little", signed=False) 
        num2 = int.from_bytes(op2, byteorder="little", signed=False)

        uns_result = num1 - num2
        if uns_result > 2**64:
            self.flags[0] += 4 #Encendemos el bit 3 carry

    def and_a(self, op1:bytearray, op2:bytearray):

        #Resetea las banderas que se pueden modificar
        self._reset_flags((3,4))

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 & num2

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)

    def or_a(self, op1:bytearray, op2:bytearray):

        #Resetea las banderas que se pueden modificar
        self._reset_flags((3,4))

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 | num2

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)

    def xor_a(self, op1:bytearray, op2:bytearray):
        #Resetea las banderas que se pueden modificar
        self._reset_flags((3,4))

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 ^ num2

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)
    
    def not_a(self, op1:bytearray):
        #Resetea las banderas que se pueden modificar
        self._reset_flags((3,4))

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 

        result = ~num1

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)

    def shl(self, op1:bytearray):
        #Resetea las banderas que se pueden modificar
        self._reset_flags((2,3,4))

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        self.acm[:] = (int.from_bytes(self.acm, byteorder="little", signed=True) << num1 - 1).to_bytes(8, byteorder='little', signed=True)
        bit = self.acm[0] & (1 << 7) == (1 << 7)

        if bit:
            self.flags[0] += 4 #Encendemos el bit 3 carry
        
        result = int.from_bytes(self.acm, byteorder="little", signed=True) << 1

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)

    def shr(self, op1:bytearray):
        #Resetea las banderas que se pueden modificar
        self._reset_flags((2,3,4))

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        self.acm[:] = (int.from_bytes(self.acm, byteorder="little", signed=True) >> num1 - 1).to_bytes(8, byteorder='little', signed=True)
        bit = self.acm[7] & (1) == (1)

        if bit:
            self.flags[0] += 4 #Encendemos el bit 3 carry
        
        result = int.from_bytes(self.acm, byteorder="little", signed=True) >> 1

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)

    def test(self, op1:bytearray, op2:bytearray):
        #Resetea las banderas que se pueden modificar
        self._reset_flags((3,4))

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 & num2

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative



if __name__ == '__main__':
    def paf(acumulador, flags):
        print(int.from_bytes(acumulador,byteorder="little", signed=True))
        print(bin(int.from_bytes(flags,byteorder="little", signed=True)))

    acumulador = bytearray(8)
    flags = bytearray(1)
    alu = ALU(acumulador, flags)
    op1 = bytearray(8)
    op1[0] = 8
    op2 = bytearray(8)
    op2[0] = 8
    alu.add(op1, op2)
    paf(acumulador, flags)
    op2[0] = 3
    alu.sub(op1, op2)
    paf(acumulador, flags)
    op2 = ((2**63)-1).to_bytes(8, byteorder="little", signed=True)
    alu.inc(op2)
    paf(acumulador, flags)
    op2 = (5).to_bytes(8, byteorder="little", signed=True)
    alu.mul(op1, op2)
    paf(acumulador, flags)
    op2 = (2).to_bytes(8, byteorder="little", signed=True)
    alu.div(op1, op2)
    paf(acumulador, flags)
    op2 = (3).to_bytes(8, byteorder="little", signed=True)
    alu.cmp(op2, op2)
    paf(acumulador, flags)
    op2 = (3).to_bytes(8, byteorder="little", signed=True)
    alu.and_a(op2, op2)
    paf(acumulador, flags)
    op2 = (3).to_bytes(8, byteorder="little", signed=True)
    alu.shl(op2)
    paf(acumulador, flags)
    alu.shr(op2)
    paf(acumulador, flags)
    
    