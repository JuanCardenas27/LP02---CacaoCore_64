

class FloatAritmethicUnit:
    def __init__(self, fp_flags, acm) -> None:
        self.fp_acm=acm
        self.flags = fp_flags 

    def _unpack(self, b_array:bytearray) -> tuple[int, int, int]:
        bin_num = bin(int.from_bytes(b_array, byteorder='little'))[2:].zfill(64)

        sign = int(bin_num[0])
        exp = int(bin_num[1:12], base=2) - 1023
        mantisa = int(bin_num[12:], base=2)
        
        return (sign, exp, mantisa)
    
    def _pack(self, sign: int, exp_insesgado:int, mantisa:int) -> bytes:
        cadena = bin(sign)[2:] + bin(exp_insesgado+1023)[2:].zfill(11) + bin(mantisa)[2:].zfill(52)
        return int(cadena, base=2).to_bytes(8, byteorder='little')
        
    
    def _check_flags(self, value):
        #TODO: Considerar al menos 5 flags usuales para float:
        # - DivZ: Inidica si hubo división por 0
        # - Overflow: Un múnero más grande del permitido
        # - Underflow: Un número tan pequeño que no sea posible ponerlo (ie 0.1x10^-100000000)
        # - InvOp: Invalid Operation, si saca raiz de un negativo por ejemplo
        # - Inex: Inexacto, se prende si el valor del resultado tiene más decimales de los que se puede expresar y debe ser redondeado (ie 1/3 eu se trunca en 0.33333333334)
        pass

    def _reset_flags(self):
        pass
    
    def fp_add(self, op1:bytearray, op2:bytearray, change_flags=True):           

        num1 = self._unpack(op1)
        num2 = self._unpack(op2)

        if num1[0] != num2[0]:
            op1[:] = self._pack(num2[0], num1[1], num1[2])
            return self.fp_sub(op1, op2)

        p_mantisa1 = (1 << 52) | num1[2]  
        p_mantisa2 = (1 << 52) | num2[2]

        dif_exp = abs(num1[1] - num2[1])
        if num1[1] > num2[1]:
            p_mantisa2 >>= dif_exp
            mayor_exp = num1[1]
        else:
            p_mantisa1 >>= dif_exp
            mayor_exp = num2[1]

        result = p_mantisa1 + p_mantisa2

        bits_extra = result.bit_length() - 53
        nuevo_expo = mayor_exp + bits_extra
        if bits_extra > 0:
            result >>= bits_extra

        mantisa_final = result & ((1 << 52) - 1)

        if change_flags:
            self._reset_flags()
            result = self._check_flags(result)

        self.fp_acm[:] = self._pack(num1[0], nuevo_expo, mantisa_final)
        return self._pack(num1[0], nuevo_expo, mantisa_final)
 

    def fp_sub(self, op1: bytearray, op2: bytearray, change_flags=True):
        num1 = self._unpack(op1)
        num2 = self._unpack(op2)

        if num1[0] != num2[0]:
            op1[:] = self._pack(num2[0], num1[1], num1[2])
            return self.fp_add(op1, op2)

        p_mantisa1 = (1 << 52) | num1[2]
        p_mantisa2 = (1 << 52) | num2[2]

        dif_exp = abs(num1[1] - num2[1])
        if num1[1] > num2[1]:
            p_mantisa2 >>= dif_exp
            mayor_exp = num1[1]
        else:
            p_mantisa1 >>= dif_exp
            mayor_exp = num2[1]

        if p_mantisa1 >= p_mantisa2:
            signo_resultado = num1[0]
        else:
            signo_resultado = 1- num1[0]

        result = p_mantisa1 - p_mantisa2

        # caso especial: resultado es exactamente cero
        if result == 0:
            return self._pack(0, -1023, 0)

        # normalizar — la resta puede encoger o crecer
        bits_resultado = result.bit_length()
        if bits_resultado < 53:
            shift = 53 - bits_resultado
            result <<= shift
            nuevo_expo = mayor_exp - shift
        else:
            nuevo_expo = mayor_exp

        mantisa_final = result & ((1 << 52) - 1)

        if change_flags:
            self._reset_flags()
            self._check_flags(result)

        self.fp_acm[:] = self._pack(signo_resultado, nuevo_expo, mantisa_final)
        return self._pack(signo_resultado, nuevo_expo, mantisa_final)
        
    @staticmethod
    def _to_binary(register:bytearray):
        """Convierte un registro a su representación de 64 bits en string.
        
        Parámetros
        ----------
        register : bytearray
            Registro a convertir.
        
        Retorna
        -------
        str
            String binario rellenado con ceros.
        """
        number = int.from_bytes(register, byteorder='little', signed=False)
        return f"{number:b}".zfill(64)

    

if __name__ == "__main__":
    flags = bytearray(1)
    acm = bytearray(8)
    objeto = FloatAritmethicUnit(flags, acm)
    import struct

    a = 1
    b = 2.1

    op1 = bytearray(struct.pack('<d', a))
    op2 = bytearray(struct.pack('<d', b))

    res = objeto.fp_div(op1, op2)
    print(struct.unpack('<d', res)[0])

