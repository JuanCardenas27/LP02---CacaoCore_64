

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
        cadena = bin(sign)[2:] + bin(exp_insesgado+1023)[2:] + bin(mantisa)[2:].zfill(52)
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
    
    def fp_div(self, op1: bytearray, op2: bytearray, change_flags=True):
        if change_flags:
            result = self._reset_flags()

        sign1, exp1, mant1 = self._unpack(op1)
        sign2, exp2, mant2 = self._unpack(op2)

        # Desnormalizar.
        mant1 |= (1 << 52)
        mant2 |= (1 << 52)

        # Signo.
        sign = sign1 ^ sign2

        # Resta de exponentes.
        exp = exp1 - exp2

        # División de mantisas.
        mant = (mant1 << 52) // mant2

        # Corrección de rango.
        if mant < (1 << 52):
            mant <<= 1
            exp -= 1
        elif mant >= (1 << 53):
            mant >>= 1
            exp += 1

        # Normalizar.
        mant &= (1 << 52) - 1

        result = self._pack(sign, exp, mant)
        self.fp_acm[:] = result

        return result


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

