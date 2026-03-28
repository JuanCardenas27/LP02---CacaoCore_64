
INF = (1024, 0)
ZERO = (0, 0)
NAN = (0, 1024, 1)
class FloatAritmethicUnit:
    def __init__(self, fp_flags, acm) -> None:
        self.fp_acm=acm
        self.flags = fp_flags
        self._invalid_ops_div = [(INF , INF), (ZERO, INF), (ZERO, ZERO)]
        self._invalid_ops_mul = [(INF , ZERO), (ZERO, INF)]
        self._invalid_ops_sum = [((1, ) + INF , (0, ) + INF), ((0, ) + INF, (1, ) + INF)]
        self._invalid_ops = {'*': self._invalid_ops_mul, '/': self._invalid_ops_div, '+': self._invalid_ops_sum}

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
        # Se encuentran el formato little endian y en el orden presentado
        

        #underflow < -1023
        #overflow > 1023
        pass
    
    def _check_0div(self, op1, op2):
        if op1[1:] == ZERO and op2[1:] == ZERO:
            self.flags[0] += 1
            self.flags[0] += 8
            return NAN #returns + or - inf
        if op2[1:] == ZERO:
            self.flags[0] += 1
            return (op1[0], ) + INF
        return False

    def _check_invalid_op(self, op1, op2, op):
        inv_op = self._invalid_ops[op]
        include_sign = 0
        if op != '+' or op != '-':
            include_sign = 1
        
        if op1[1] == 1024 and op1[2] != 0:
            self.flags[0] += 8
            return NAN
        if op2[1] == 1024 and op2[2] != 0:
            self.flags[0] += 8
            return NAN
        if (op1[include_sign:], op2[include_sign:]) not in inv_op:
            self.flags[0] += 8
            return NAN
        return False

    def _check_overflow(self, sign, exp):
        if exp > 1023:
            self.flags[0] += 2
            return (sign, ) + INF
        return False

    def _check_underflow(self, sign, exp):
        if exp < -1022:
            self.flags[0] += 4
            return (sign, ) + ZERO
        return False

    def _reset_flags(self):
        self.flags[:] = (0).to_bytes(1)
        pass
    
    def fp_add(self, op1:bytearray, op2:bytearray):           
        
        num1 = self._unpack(op1)
        num2 = self._unpack(op2)

        #Check Inv Operands
        
        self._reset_flags()
        result = self._check_invalid_op(num1, num2, '+')
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result

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

        
        self._reset_flags()
        #Check Overflow
        result = self._check_overflow(sign, exponente)
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result
        
        #Check Underflow
        result = self._check_underflow(sign, exponente)
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result
        

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
            signo_resultado = 1 - num1[0]

        result = p_mantisa1 - p_mantisa2

        # caso especial: resultado es exactamente cero
        if result == 0:
            return self._pack(0, -1023, 0)

        # normalizar — la resta puede encoger la mantisa
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
    
    def fp_mul(self, op1:bytearray, op2:bytearray, change_flags=True):
        if change_flags:
            self._reset_flags()
        
        parts_op1 = self._unpack(op1)
        parts_op2 = self._unpack(op2)
        
        #Check inv Operands
        result = self._check_invalid_op(parts_op1, parts_op2, '*')
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result
            

        sign = parts_op1[0] ^ parts_op2[0]
        exponente = parts_op1[1] + parts_op2[1] 

        mA_full = (1 << 52) | parts_op1[2]
        mB_full = (1 << 52) | parts_op2[2]
        mantisa = mA_full * mB_full

        if mantisa.bit_length() == 106:
            mantisa >>= 1
            exponente += 1

        #round
        m = (mantisa >> 52) & ((1 << 52) - 1) 

        G = (mantisa >> 51) & 1
        R = (mantisa >> 50) & 1
        S = (mantisa & ((1 << 50) - 1)) != 0
        
        if G:
            self.flags[0] += 16
            if R or S:
                m += 1              # > 0.5 ULP
            else:
                if m & 1:           # impar round-to-even
                    m += 1

        if m == (1 << 52):          # desbordamiento del redondeo
            m = 0
            exponente += 1

        #Check Overflow
        result = self._check_overflow(sign, exponente)
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result
        
        #Check Underflow
        result = self._check_underflow(sign, exponente)
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result

        result = self._pack(sign, exponente, m)
        self.fp_acm[:] = result
        return result

    def fp_div(self, op1: bytearray, op2: bytearray, change_flags=True):
        if change_flags:
            result = self._reset_flags()

        unp1 = self._unpack(op1)
        unp2 = self._unpack(op2)
        sign1, exp1, mant1 = unp1
        sign2, exp2, mant2 = unp2

        #Check DIV0
        result = self._check_0div(unp1, unp2)
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result
        
        #Check inv operands
        result = self._check_invalid_op(unp1, unp2, '/')
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result
        
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
            self.flags[0] += 16
            mant <<= 1
            exp -= 1
        elif mant >= (1 << 53):
            self.flags[0] += 16
            mant >>= 1
            exp += 1

        # Normalizar.
        mant &= (1 << 52) - 1

        #Check Overflow
        result = self._check_overflow(sign, exp)
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result
        
        #Check Underflow
        result = self._check_underflow(sign, exp)
        if result:
            result = self._pack(*result)
            self.fp_acm[:] = result
            return result
        
        result = self._pack(sign, exp, mant)
        self.fp_acm[:] = result

        return result

        
    def fp_cmp(self, op1:bytearray, op2:bytearray):
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

        # normalizar — la resta puede encoger la mantisa
        bits_resultado = result.bit_length()
        if bits_resultado < 53:
            shift = 53 - bits_resultado
            result <<= shift
            nuevo_expo = mayor_exp - shift
        else:
            nuevo_expo = mayor_exp

        mantisa_final = result & ((1 << 52) - 1)

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

    a = 2.5
    b = -2.5

    op1 = bytearray(struct.pack('<d', a))
    op2 = bytearray(struct.pack('<d', b))

    res = objeto.fp_sub(op1, op2)
    print(struct.unpack('<d', res)[0])

