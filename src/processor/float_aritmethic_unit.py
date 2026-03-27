

class FloatAritmethicUnit:
    def __init__(self, fp_flags, acm) -> None:
        self.fp_acm=acm
        self.flags = fp_flags 

    def _unpack(self, bin_num:str) -> tuple[int, int, int]:
        sign = int(bin_num[0])
        exp = int(bin_num[1:12], base=2) - 1023
        mantisa = int(bin_num[12:], base=2)
        
        return (sign, exp, mantisa)
    
    def _pack(self, sign: int, exp_insesgado:int, mantisa:int) -> str:
        return bin(sign)[2:] + bin(exp_insesgado+1023)[2:] + bin(mantisa)[2:].zfill(64)
    
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

        self.fp_acm[:] = result.to_bytes(8, byteorder='little', signed=True)


    
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
    objeto = FloatAritmethicUnit(flags)
    var = "0100000000100100111000001100010010011011101001011110001101010100"
    tupla = objeto._unpack(var)
    # 0100000000100100111000001100010010011011101001011110001101010100
    # 0100000000100100111000001100010010011011101001011110001101010100
    print(tupla)
    print(objeto._pack(*tupla))
    x=10
    print(-6<=x<=6)


    