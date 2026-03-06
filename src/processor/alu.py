"""Arithmetic Logic Unit (ALU) Module
===========================================

Implementa la Unidad Aritmético-Lógica del procesador Cacao Core 64.

Realiza operaciones aritméticas (suma, resta, multiplicación, división),
lógicas (AND, OR, XOR, NOT) y de desplazamiento (SHL, SHR) en operandos
de 64 bits. Mantiene flags de estado (overflow, zero, negative, carry).

Objetos
-------
ALU : Clase principal que implementa todas las operaciones ALU.

Ejemplo de uso:
    alu = ALU(acumulador, flags)
    alu.add(operando1, operando2)  # Suma dos operandos
    alu.mul(operando1, operando2)  # Multiplica dos operandos
"""

class ALU: 
    """Unidad Aritmético-Lógica del procesador Cacao Core 64.
    
    Realiza operaciones aritméticas, lógicas y de desplazamiento, manteniendo
    flags de estado (overflow, zero, negative, carry) tras cada operación.
    
    Atributos
    ---------
    acm : bytearray
        Acumulador de 8 bytes (64 bits) donde se almacenan resultados.
    flags : bytearray
        Registro de flags de 1 byte con los siguientes bits:
        - Bit 0: Interrupt Enable (I)
        - Bit 1: Overflow (V)
        - Bit 2: Carry (C)
        - Bit 3: Negative (N)
        - Bit 4: Zero (Z)
    """
    def __init__(self, acumulator, flags):
        """Inicializa la ALU.
        
        Parámetros
        ----------
        acumulator : bytearray
            Referencia al acumulador de 8 bytes.
        flags : bytearray
            Referencia al registro de flags de 1 byte.
        """
        self.acm = acumulator
        self.flags = flags 

    def _check_flags(self, result):
        """Verifica y actualiza flags de estado según el resultado.
        
        Actualiza los flags de Overflow (V), Zero (Z) y Negative (N) según
        el resultado de una operación.
        
        Parámetros
        ----------
        result : int
            Resultado de la operación a verificar.
        
        Retorna
        -------
        int
            Resultado ajustado a 64 bits si hay overflow.
        """
        if result >= 2**63 or result < -2**63:
            self.flags[0] += 2 #Encendemos el bit 2 overflow
            result = int.from_bytes(result.to_bytes(9, byteorder='little', signed=True)[0:8], byteorder="little", signed=True)

        if result == 0:
            self.flags[0] += 16 #Encendemos el bit 5 zero

        if result < 0:
            self.flags[0] += 8 #Encendemos el bit 4 negative
        
        return result

    def _reset_flags(self, positions = (1,2,3,4)):
        """Limpia (resetea) bits de flags especificados.
        
        Parámetros
        ----------
        positions : tuple, opcional
            Posiciones de bits a resetear. Por defecto (1,2,3,4) que corresponden
            a Overflow, Carry, Negative y Zero.
        """
        for i in positions:
            self.flags[0] &= ~(1 << i)

    def add(self, op1:bytearray, op2:bytearray, change_flags=True):
        """Suma dos operandos de 64 bits.
        
        Realiza una suma signada y sin signo, verificando overflow y carry.
        Actualiza flags V, C, Z y N. El resultado se almacena en el acumulador.
        
        Parámetros
        ----------
        op1 : bytearray
            Primer operando de 8 bytes.
        op2 : bytearray
            Segundo operando de 8 bytes.
        """
        #Resetea las banderas que se pueden modificar
        if change_flags:
            self._reset_flags()

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 + num2
        if change_flags:
            result = self._check_flags(result)

        num1 = int.from_bytes(op1, byteorder="little", signed=False) 
        num2 = int.from_bytes(op2, byteorder="little", signed=False)

        uns_result = num1 + num2
        if uns_result > 2**64:
            self.flags[0] += 4 #Encendemos el bit 3 carry

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)

    def sub(self, op1:bytearray, op2:bytearray):
        """Resta dos operandos de 64 bits (op1 - op2).
        
        Realiza una resta signada y sin signo, verificando overflow y carry.
        Actualiza flags V, C, Z y N. El resultado se almacena en el acumulador.
        
        Parámetros
        ----------
        op1 : bytearray
            Minuendo de 8 bytes.
        op2 : bytearray
            Sustraendo de 8 bytes.
        """
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
        """Incrementa un operando de 64 bits en 1.
        
        Equivale a add(op1, 1). Actualiza los mismos flags que add.
        
        Parámetros
        ----------
        op1 : bytearray
            Operando de 8 bytes a incrementar.
        """
        #Resetea las banderas que se pueden modificar
        self.add(op1, bytearray((1).to_bytes(8, byteorder='little', signed=True)))
    
    def mul(self, op1:bytearray, op2:bytearray):
        """Multiplica dos operandos de 64 bits.
        
        Realiza una multiplicación signada. Actualiza flags V, Z y N.
        El resultado se almacena en el acumulador.
        
        Parámetros
        ----------
        op1 : bytearray
            Primer operando de 8 bytes.
        op2 : bytearray
            Segundo operando de 8 bytes.
        """
        #Resetea las banderas que se pueden modificar
        
        self._reset_flags()

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 * num2

        result = self._check_flags(result)

        self.acm[:] = result.to_bytes(8, byteorder='little', signed=True)
    
    def div(self, op1:bytearray, op2:bytearray):
        """Divide dos operandos de 64 bits (op1 / op2).
        
        Realiza una división entera signada. El cociente se almacena en el
        acumulador. Actualiza flags Z y N. Retorna el residuo.
        
        Parámetros
        ----------
        op1 : bytearray
            Dividendo de 8 bytes.
        op2 : bytearray
            Divisor de 8 bytes.
        
        Retorna
        -------
        int
            Residuo de la división (op1 % op2).
        """
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
        """Decrementa un operando de 64 bits en 1.
        
        Equivale a sub(op1, 1). Actualiza los mismos flags que sub.
        
        Parámetros
        ----------
        op1 : bytearray
            Operando de 8 bytes a decrementar.
        """
        #Resetea las banderas que se pueden modificar
        self.sub(op1, bytearray((1).to_bytes(8, byteorder='little', signed=True)))

    def cmp(self, op1:bytearray, op2:bytearray):
        """Compara dos operandos (op1 - op2) sin guardar resultado.
        
        Realiza una resta para actualizar flags, pero no modifica el acumulador.
        Útil para comparaciones en saltos condicionales.
        
        Parámetros
        ----------
        op1 : bytearray
            Primer operando de 8 bytes.
        op2 : bytearray
            Segundo operando de 8 bytes.
        """
        #Resetea las banderas que se pueden modificar
        self._reset_flags()

        num1 = int.from_bytes(op1, byteorder="little", signed=True) 
        num2 = int.from_bytes(op2, byteorder="little", signed=True)

        result = num1 - num2
        print(result)
        result = self._check_flags(result)

        num1 = int.from_bytes(op1, byteorder="little", signed=False) 
        num2 = int.from_bytes(op2, byteorder="little", signed=False)

        uns_result = num1 - num2
        if uns_result > 2**64:
            self.flags[0] += 4 #Encendemos el bit 3 carry

    def and_a(self, op1:bytearray, op2:bytearray):
        """Operación AND bit a bit de dos operandos.
        
        Realiza una AND lógica entre dos operandos de 64 bits.
        Actualiza flags Z y N. El resultado se almacena en el acumulador.
        
        Parámetros
        ----------
        op1 : bytearray
            Primer operando de 8 bytes.
        op2 : bytearray
            Segundo operando de 8 bytes.
        """
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
        """Operación OR bit a bit de dos operandos.
        
        Realiza una OR lógica entre dos operandos de 64 bits.
        Actualiza flags Z y N. El resultado se almacena en el acumulador.
        
        Parámetros
        ----------
        op1 : bytearray
            Primer operando de 8 bytes.
        op2 : bytearray
            Segundo operando de 8 bytes.
        """
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
        """Operación XOR bit a bit de dos operandos.
        
        Realiza una XOR lógica entre dos operandos de 64 bits.
        Actualiza flags Z y N. El resultado se almacena en el acumulador.
        
        Parámetros
        ----------
        op1 : bytearray
            Primer operando de 8 bytes.
        op2 : bytearray
            Segundo operando de 8 bytes.
        """
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
        """Operación NOT bit a bit (complemento lógico).
        
        Realiza una NOT lógica bit a bit del operando de 64 bits.
        Actualiza flags Z y N. El resultado se almacena en el acumulador.
        
        Parámetros
        ----------
        op1 : bytearray
            Operando de 8 bytes.
        """
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
        """Desplazamiento a la izquierda (Shift Left).
        
        Desplaza los bits del acumulador hacia la izquierda, usando op1
        como el número de posiciones a desplazar. El bit más significativo
        se descarta en Carry. Actualiza flags C, Z y N.
        
        Parámetros
        ----------
        op1 : bytearray
            Operando de 8 bytes indicando número de posiciones de desplazamiento.
        """
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
        """Desplazamiento a la derecha (Shift Right).
        
        Desplaza los bits del acumulador hacia la derecha, usando op1
        como el número de posiciones a desplazar. El bit menos significativo
        se descarta en Carry. Actualiza flags C, Z y N.
        
        Parámetros
        ----------
        op1 : bytearray
            Operando de 8 bytes indicando número de posiciones de desplazamiento.
        """
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
        """Prueba AND sin guardar resultado.
        
        Realiza una AND lógica entre dos operandos para actualizar flags,
        pero no modifica el acumulador. Útil para verificar bits.
        
        Parámetros
        ----------
        op1 : bytearray
            Primer operando de 8 bytes.
        op2 : bytearray
            Segundo operando de 8 bytes.
        """
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
    op2 = bytearray(((2**63)-1).to_bytes(8, byteorder="little", signed=True))
    alu.inc(op2)
    paf(acumulador, flags)
    op2 = bytearray((5).to_bytes(8, byteorder="little", signed=True))
    alu.mul(op1, op2)
    paf(acumulador, flags)
    op2 = bytearray((2).to_bytes(8, byteorder="little", signed=True))
    alu.div(op1, op2)
    paf(acumulador, flags)
    op2 = bytearray((3).to_bytes(8, byteorder="little", signed=True))
    alu.cmp(op2, op2)
    paf(acumulador, flags)
    op2 = bytearray((3).to_bytes(8, byteorder="little", signed=True))
    alu.and_a(op2, op2)
    paf(acumulador, flags)
    op2 = bytearray((3).to_bytes(8, byteorder="little", signed=True))
    alu.shl(op2)
    paf(acumulador, flags)
    alu.shr(op2)
    paf(acumulador, flags)
    
    