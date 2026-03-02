from memoria.ram import VECTOR_TABLE
HALTED = 0

class MicroinstructionMixin:
    #################################
    #       MICROINSTRUCCIONES      #
    #################################

    def hlt(self):
        """HALT - Detiene la ejecución del procesador."""
        self.state = HALTED
        print("System HALTED. Fin de la ejecución")
    
    def mov_ra(self, op1, op2, size):
        """MOV registro-acumulador: op1 = op2.
        
        Copia el valor de op2 al operando op1 (acumulador o registro).
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Destino (registro o acumulador).
        op2 : bytearray
            Fuente (valor o registro).
        size : int
            Tamaño en bits del operando.
        """
        value = self.bytes_to_int(op2)
        op1[:] = self.int_to_bytes(value, size)

    def mov_rm(self, op1, op2, size):
        """MOV registro-memoria: op1 = [op2].
        
        Lee datos desde memoria en la dirección op2 y los copia a op1.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Destino (registro).
        op2 : bytearray
            Dirección de memoria.
        size : int
            Tamaño en bits del operando.
        """
        self._mar[:]=op2[:]
        self._read_from_ram(size=size//8)
        value = self.bytes_to_int(self._mdr)
        op1[:] = self.int_to_bytes(value, size)

    def mov_ma(self, op1, op2, size):
        """MOV memoria-acumulador: [op1] = op2.
        
        Copia el valor de op2 a la dirección de memoria op1.
        Modos: mr (memoria-registro) o mi (memoria-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        op2 : bytearray
            Valor a escribir.
        size : int
            Tamaño en bits del operando.
        """
        value = self.bytes_to_int(op2)
        self._mdr[:] = self.int_to_bytes(value, size)
        self._mar[:] = op1[:]
        self._write_to_ram(size=size//8)

    def load_m(self, op1, size):
        """LOAD memoria: ACM = [op1].
        
        Lee datos desde memoria en la dirección op1 y los carga en el acumulador.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        size : int
            Tamaño en bits del operando.
        """
        self._mar[:] = op1[:]
        self._read_from_ram(size=size//8)
        value = self.bytes_to_int(self._mdr)
        self._registers[15][:] = self.int_to_bytes(value, size)
    
    def load_i(self, op1, size):
        """LOAD inmediato: ACM = op1.
        
        Carga un valor inmediato en el acumulador.
        Modo: i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor inmediato a cargar.
        size : int
            Tamaño en bits del operando.
        """
        value = self.bytes_to_int(op1)
        self._registers[15][:] = self.int_to_bytes(value, size)

    def load_rm(self, op1, op2, size):
        """LOAD registro-memoria: op1 = [op2].
        
        Lee datos desde memoria en la dirección op2 y los carga en op1.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Dirección de memoria.
        size : int
            Tamaño en bits del operando.
        """
        self._mar[:] = op2[:]
        self._read_from_ram(size=size//8)
        value = self.bytes_to_int(self._mdr)
        op1[:] = self.int_to_bytes(value, size)

    def load_ri(self, op1, op2, size):
        """LOAD registro-inmediato: op1 = op2.
        
        Carga un valor inmediato en un registro.
        Modo: ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Valor inmediato.
        size : int
            Tamaño en bits del operando.
        """
        value = self.bytes_to_int(op2)
        op1[:] = self.int_to_bytes(value, size)
    
    def store_m(self, op1, size):
        """STORE memoria: [op1] = ACM.
        
        Escribe el valor del acumulador en memoria en la dirección op1.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        size : int
            Tamaño en bits del operando.
        """
        value = self.bytes_to_int(self._registers[15])
        self._mdr[:] = self.int_to_bytes(value, size)
        self._mar[:] = op1[:]
        self._write_to_ram(size=size//8)
    
    def store_r(self, op1, size):
        """STORE registro: op1 = ACM.
        
        Copia el valor del acumulador a un registro.
        Modo: r (registro).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        size : int
            Tamaño en bits del operando.
        """
        value = self.bytes_to_int(self._registers[15])
        op1[:] = self.int_to_bytes(value, size)

    def store_ma(self, op1, op2, size):
        """STORE memoria-acumulador: [op1] = op2.
        
        Escribe el valor de op2 en memoria en la dirección op1.
        Modos: mr (memoria-registro) o mi (memoria-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        op2 : bytearray
            Valor a escribir.
        size : int
            Tamaño en bits del operando.
        """
        value = self.bytes_to_int(op2)
        self._mdr[:] = self.int_to_bytes(value, size)
        self._mar[:] = op1[:]
        self._write_to_ram(size=size//8)

    def jmp(self, op1):
        """JMP - Salto incondicional.
        
        Salta a la dirección especificada en op1 actualizando PC.
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de salto.
        """
        self._pc = op1[:]
    
    def j_condicional(self, op1, flag):
        """JZ/JS/JC/JV/JI - Salto condicional si flag activo.
        
        Salta a la dirección op1 si el flag especificado está activo.
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de salto.
        flag : str
            Flag a verificar ('z'=zero, 's'=sign, 'c'=carry, 'v'=overflow, 'i'=interrupt).
        """
        index = self._flags_indexes[flag]
        flags = self._to_binary(self._fr, 8, False)
        if int(flags[index]):
            self._pc = op1[:]

    def jn_condicional(self, op1, flag):
        """JNZ/JNS/JNC/JNV/JNI - Salto condicional si flag inactivo.
        
        Salta a la dirección op1 si el flag especificado está inactivo.
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de salto.
        flag : str
            Flag a verificar ('z'=zero, 's'=sign, 'c'=carry, 'v'=overflow, 'i'=interrupt).
        """
        index = self._flags_indexes[flag]
        flags = self._to_binary(self._fr, 8, False)
        if not int(flags[index]):
            self._pc = op1[:]

    def j_comparacion(self, op1, flag1, flag2, cmp):
        """Salto condicional basado en comparación de dos flags.
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de salto.
        flag1 : str
            Primer flag.
        flag2 : str
            Segundo flag.
        cmp : str
            Operador de comparación.
        """
        pass

    def call_m(self, op1):
        """CALL - Llamada a subrutina.
        
        Guarda PC en Link Register (R14), empieza la subrutina en op1.
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de la subrutina.
        """
        self._registers[14][:] = self._pc[:]
        self.push(op1)
        self.jmp(op1)
    
    def ret(self):
        """RET - Retorno de subrutina.
        
        Recupera la dirección de retorno del Link Register y actualiza PC.
        """
        self.pop(self._registers[14])
        self._pc[:] = self._registers[14][:]
    
    def push(self, op1):
        """PUSH - Empilar un valor en la pila.
        
        Escribe op1 en la dirección del Stack Pointer y decrementa SP.
        
        Parámetros
        ----------
        op1 : bytearray
            Valor a empilar (8 bytes).
        """
        self._mar[:] = self._registers[13][:]
        self._mdr[:] = op1[:]
        self._write_to_ram()
        head_sp = self.bytes_to_int(self._registers[13], False)
        head_sp -= 8
        self._registers[13][:] = self.int_to_bytes(head_sp, 64)
    
    def pop(self, op1):
        """POP - Desempilar un valor de la pila.
        
        Lee desde la dirección del Stack Pointer a op1 e incrementa SP.
        
        Parámetros
        ----------
        op1 : bytearray
            Ubicación donde guardar el valor desempilado.
        """
        self._mar[:] = self._registers[13][:]
        self._read_from_ram()
        op1[:] = self._mdr[:]
        head_sp = self.bytes_to_int(self._registers[13], False)
        head_sp += 8
        self._registers[13][:] = self.int_to_bytes(head_sp, 64)
    
    def iret(self):
        """IRET - Retorno de manejador de interrupción.
        
        Restaura el estado completo del procesador desde la pila:
        PC, FR, y todos los registros.
        """
        for reg in range(15,0, -1):
            self.pop(self._registers[reg])
        self.pop(self._fr)
        self.pop(self._pc)
    
    def int(self):
        """INT - Generar interrupción de software."""
        pass

    def nop(self):
        """NOP - Operación nula (sin operación)."""
        pass
    
    def ei(self):
        """EI - Habilitar interrupciones.
        
        Activa el bit de habilitar interrupciones (bit 0 de FR).
        """
        flags = int.from_bytes(self._fr, byteorder='little', signed=False)
        flags |= 1
        self._fr[:] = flags.to_bytes(1, byteorder='little', signed=False)

    def di(self):
        """DI - Deshabilitar interrupciones.
        
        Desactiva el bit de habilitar interrupciones (bit 0 de FR).
        """
        flags = int.from_bytes(self._fr, byteorder='little', signed=False)
        flags &= ~1
        self._fr[:] = flags.to_bytes(1, byteorder='little', signed=False)
        
    def sext(self):
        pass

    def neg(self):
        pass
        self._write_to_ram()

    #Operaciones aritmeticas
    def add_m(self, op1):
        """ADD memoria: ACM = ACM + [op1].
        
        Suma el contenido de memoria a el acumulador.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.add(self._registers[15], self._mdr)

    def add_a(self, op1):
        """ADD acumulador: ACM = ACM + op1.
        
        Suma un valor (registro o inmediato) al acumulador.
        Modos: r (registro) o i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor a sumar.
        """
        self._alu.add(self._registers[15], op1)

    def add_ra(self, op1, op2):
        """ADD registro-acumulador: op1 = op1 + op2.
        
        Suma dos valores (registros o inmediatos).
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Valor a sumar.
        """
        self._alu.add(op1, op2)
        op1[:] = self._registers[15][:]
    
    def add_rm(self, op1, op2):
        """ADD registro-memoria: op1 = op1 + [op2].
        
        Suma el contenido de memoria a un registro.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.add(op1, self._mdr)
        op1[:] = self._registers[15][:]


    def sub_m(self, op1):
        """SUB memoria: ACM = ACM - [op1].
        
        Resta el contenido de memoria al acumulador.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.sub(self._registers[15], self._mdr)

    def sub_a(self, op1):
        """SUB acumulador: ACM = ACM - op1.
        
        Resta un valor (registro o inmediato) al acumulador.
        Modos: r (registro) o i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor a restar.
        """
        self._alu.sub(self._registers[15], op1)

    def sub_ra(self, op1, op2):
        """SUB registro-acumulador: op1 = op1 - op2.
        
        Resta dos valores (registros o inmediatos).
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Valor a restar.
        """
        self._alu.sub(op1, op2)
        op1[:] = self._registers[15][:]
    
    def sub_rm(self, op1, op2):
        """SUB registro-memoria: op1 = op1 - [op2].
        
        Resta el contenido de memoria a un registro.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.sub(op1, self._mdr)
        op1[:] = self._registers[15][:]

    
    def mul_m(self, op1):
        """MUL memoria: ACM = ACM * [op1].
        
        Multiplica el acumulador por el contenido de memoria.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.mul(self._registers[15], self._mdr)

    def mul_a(self, op1):
        """MUL acumulador: ACM = ACM * op1.
        
        Multiplica el acumulador por un valor (registro o inmediato).
        Modos: r (registro) o i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor a multiplicar.
        """
        self._alu.mul(self._registers[15], op1)

    def mul_ra(self, op1, op2):
        """MUL registro-acumulador: op1 = op1 * op2.
        
        Multiplica dos valores (registros o inmediatos).
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Valor a multiplicar.
        """
        self._alu.mul(op1, op2)
        op1[:] = self._registers[15][:]
    
    def mul_rm(self, op1, op2):
        """MUL registro-memoria: op1 = op1 * [op2].
        
        Multiplica un registro por el contenido de memoria.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.mul(op1, self._mdr)
        op1[:] = self._registers[15][:]

    
    def div_m(self, op1):
        """DIV memoria: ACM = ACM / [op1].
        
        Divide el acumulador por el contenido de memoria.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.div(self._registers[15], self._mdr)

    def div_a(self, op1):
        """DIV acumulador: ACM = ACM / op1.
        
        Divide el acumulador por un valor (registro o inmediato).
        Modos: r (registro) o i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Divisor.
        """
        self._alu.div(self._registers[15], op1)

    def div_ra(self, op1, op2):
        """DIV registro-acumulador: op1 = op1 / op2.
        
        Divide dos valores (registros o inmediatos).
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino (dividendo).
        op2 : bytearray
            Divisor.
        """
        self._alu.div(op1, op2)
        op1[:] = self._registers[15][:]
    
    def div_rm(self, op1, op2):
        """DIV registro-memoria: op1 = op1 / [op2].
        
        Divide un registro por el contenido de memoria.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino (dividendo).
        op2 : bytearray
            Dirección de memoria (divisor).
        """
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.div(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def inc_r(self, op1):
        """INC registro: op1 = op1 + 1.
        
        Incrementa un registro.
        Modo: r (registro).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro a incrementar.
        """
        self._alu.inc(op1)

    def inc_m(self, op1):
        """INC memoria: [op1] = [op1] + 1.
        
        Incrementa el contenido de una ubicación de memoria.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.inc(self._mdr)

    def dec_r(self, op1):
        """DEC registro: op1 = op1 - 1.
        
        Decrementa un registro.
        Modo: r (registro).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro a decrementar.
        """
        self._alu.dec(op1)

    def dec_m(self, op1):
        """DEC memoria: [op1] = [op1] - 1.
        
        Decrementa el contenido de una ubicación de memoria.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.dec(self._mdr)

    def and_m(self, op1):
        """AND memoria: ACM = ACM AND [op1].
        
        Realiza AND lógica entre acumulador y contenido de memoria.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.and_a(self._registers[15], self._mdr)

    def and_a(self, op1):
        """AND acumulador: ACM = ACM AND op1.
        
        Realiza AND lógica entre acumulador y un valor.
        Modos: r (registro) o i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor a operar.
        """
        self._alu.and_a(self._registers[15], op1)

    def and_ra(self, op1, op2):
        """AND registro-acumulador: op1 = op1 AND op2.
        
        Realiza AND lógica entre dos valores.
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Valor a operar.
        """
        self._alu.and_a(op1, op2)
        op1[:] = self._registers[15][:]
    
    def and_rm(self, op1, op2):
        """AND registro-memoria: op1 = op1 AND [op2].
        
        Realiza AND lógica entre registro y contenido de memoria.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.and_a(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def or_m(self, op1):
        """OR memoria: ACM = ACM OR [op1].
        
        Realiza OR lógica entre acumulador y contenido de memoria.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.or_a(self._registers[15], self._mdr)

    def or_a(self, op1):
        """OR acumulador: ACM = ACM OR op1.
        
        Realiza OR lógica entre acumulador y un valor.
        Modos: r (registro) o i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor a operar.
        """
        self._alu.or_a(self._registers[15], op1)

    def or_ra(self, op1, op2):
        """OR registro-acumulador: op1 = op1 OR op2.
        
        Realiza OR lógica entre dos valores.
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Valor a operar.
        """
        self._alu.or_a(op1, op2)
        op1[:] = self._registers[15][:]
    
    def or_rm(self, op1, op2):
        """OR registro-memoria: op1 = op1 OR [op2].
        
        Realiza OR lógica entre registro y contenido de memoria.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.or_a(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def xor_m(self, op1):
        """XOR memoria: ACM = ACM XOR [op1].
        
        Realiza XOR lógica entre acumulador y contenido de memoria.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.xor_a(self._registers[15], self._mdr)

    def xor_a(self, op1):
        """XOR acumulador: ACM = ACM XOR op1.
        
        Realiza XOR lógica entre acumulador y un valor.
        Modos: r (registro) o i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor a operar.
        """
        self._alu.xor_a(self._registers[15], op1)

    def xor_ra(self, op1, op2):
        """XOR registro-acumulador: op1 = op1 XOR op2.
        
        Realiza XOR lógica entre dos valores.
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Valor a operar.
        """
        self._alu.xor_a(op1, op2)
        op1[:] = self._registers[15][:]
    
    def xor_rm(self, op1, op2):
        """XOR registro-memoria: op1 = op1 XOR [op2].
        
        Realiza XOR lógica entre registro y contenido de memoria.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.xor_a(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def not_m(self, op1):
        """NOT memoria: [op1] = NOT [op1].
        
        Realiza NOT lógica del contenido de memoria.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.not_a(self._mdr)

    def not_r(self, op1):
        """NOT registro: op1 = NOT op1.
        
        Realiza NOT lógica de un registro.
        Modo: r (registro).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro a operar.
        """
        self._alu.not_a(op1)

    def cmp_m(self, op1):
        """CMP memoria: actualiza flags comparando ACM con [op1].
        
        Compara acumulador con contenido de memoria sin modificar ACM.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.cmp(self._registers[15], self._mdr)

    def cmp_a(self, op1):
        """CMP acumulador: actualiza flags comparando ACM con op1.
        
        Compara acumulador con un valor sin modificar ACM.
        Modos: r (registro) o i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor a comparar.
        """
        self._alu.cmp(self._registers[15], op1)

    def cmp_ra(self, op1, op2):
        """CMP registro-acumulador: actualiza flags comparando op1 con op2.
        
        Compara dos valores sin modificar ningún registro.
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Primer operando.
        op2 : bytearray
            Segundo operando.
        """
        self._alu.cmp(op1, op2)
        op1[:] = self._registers[15][:]
    
    def cmp_rm(self, op1, op2):
        """CMP registro-memoria: actualiza flags comparando op1 con [op2].
        
        Compara un registro con contenido de memoria sin modificar registros.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro a comparar.
        op2 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.cmp(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def test_m(self, op1):
        """TEST memoria: actualiza flags con AND(ACM, [op1]) sin modificar ACM.
        
        Prueba bits de ACM con contenido de memoria.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.test(self._registers[15], self._mdr)

    def test_a(self, op1):
        """TEST acumulador: actualiza flags con AND(ACM, op1) sin modificar ACM.
        
        Prueba bits de ACM con un valor.
        Modos: r (registro) o i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor a operar.
        """
        self._alu.test(self._registers[15], op1)

    def test_ra(self, op1, op2):
        """TEST registro-acumulador: actualiza flags con AND(op1, op2) sin modificar.
        
        Prueba bits entre dos valores.
        Modos: rr (registro-registro) o ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Primer operando.
        op2 : bytearray
            Segundo operando.
        """
        self._alu.test(op1, op2)
        op1[:] = self._registers[15][:]
    
    def test_rm(self, op1, op2):
        """TEST registro-memoria: actualiza flags con AND(op1, [op2]) sin modificar.
        
        Prueba bits de un registro con contenido de memoria.
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro a probar.
        op2 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.test(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def shl_i(self, op1):
        """SHL inmediato: Desplazamiento a la izquierda del ACM.
        
        Desplaza el acumulador hacia la izquierda usando el valor inmediato.
        Modo: i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Número de posiciones a desplazar.
        """
        self._alu.shl(op1)

    def shl_ri(self, op1, op2):
        """SHL registro-inmediato: Desplazamiento a la izquierda de un registro.
        
        Carga un valor inmediato y desplaza un registro.
        Modo: ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor inmediato del desplazamiento.
        op2 : bytearray
            Registro a desplazar.
        """
        self.load_i(op1, 8)
        self._alu.shl(op2)
        op1[:] = self._registers[15][:]

    def shr_i(self, op1):
        """SHR inmediato: Desplazamiento a la derecha del ACM.
        
        Desplaza el acumulador hacia la derecha usando el valor inmediato.
        Modo: i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Número de posiciones a desplazar.
        """
        self._alu.shr(op1)

    def shr_ri(self, op1, op2):
        """SHR registro-inmediato: Desplazamiento a la derecha de un registro.
        
        Carga un valor inmediato y desplaza un registro.
        Modo: ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Valor inmediato del desplazamiento.
        op2 : bytearray
            Registro a desplazar.
        """
        self.load_i(op1, 8)
        self._alu.shr(op2)
        op1[:] = self._registers[15][:]

    def swap_r(self, op1):
        """SWAP registro: Intercambia un registro con el ACM.
        
        Realiza un intercambio entre el ACM y el registro especificado.
        Modo: r (registro).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro a intercambiar con ACM.
        """
        temp = op1[:]
        op1[:] = self._registers[15][:]
        self._registers[15][:] = temp

    def swap_rr(self, op1, op2):
        """SWAP registro-registro: Intercambia dos registros.
        
        Realiza un intercambio entre dos registros.
        Modo: rr (registro-registro).
        
        Parámetros
        ----------
        op1 : bytearray
            Primer registro.
        op2 : bytearray
            Segundo registro.
        """
        temp = op1[:]
        op1[:] = op2[:]
        op2[:] = temp

    def lea_m(self, op1):
        """LEA memoria: Carga dirección efectiva (address).
        
        Carga una dirección en el acumulador (sin leer contenido).
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección a cargar.
        """
        self.load_i(op1, 32)

    def lea_rm(self, op1, op2):
        """LEA registro-memoria: Carga dirección efectiva en un registro.
        
        Carga una dirección en el registro especificado (sin leer contenido).
        Modo: rm (registro-memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro destino.
        op2 : bytearray
            Dirección a cargar.
        """
        self.load_i(op2, 32)
        op1[:] = self._registers[15][:]

    def ror_i(self, op1):
        """ROR inmediato: Rotación a la derecha del ACM.
        
        Realiza una rotación circular a la derecha del acumulador.
        Modo: i (inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Número de posiciones a rotar.
        """
        value = self.bytes_to_int(self._registers[15])
        shift = self.bytes_to_int(op1)
        tmp = (value >> shift) | ((value << (8 - shift)) & (2**8 - 1))
        self._registers[15][:] = self.int_to_bytes(tmp, 64)
    
    def ror_ri(self, op1, op2):
        """ROR registro-inmediato: Rotación a la derecha de un registro.
        
        Realiza una rotación circular a la derecha de un registro.
        Modo: ri (registro-inmediato).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro a rotar.
        op2 : bytearray
            Número de posiciones a rotar.
        """
        value = self.bytes_to_int(op1)
        shift = self.bytes_to_int(op2)
        op1[:] = (value >> shift) | ((value << (8 - shift)) & (2**8 - 1))

    def cmpz_r(self, op1):
        """CMPZ registro: Compara un registro con cero.
        
        Compara un registro con el valor cero actualizando flags.
        Modo: r (registro).
        
        Parámetros
        ----------
        op1 : bytearray
            Registro a comparar.
        """
        self.cmp_ra(self.int_to_bytes(0, 8), op1)

    def cmpz_m(self, op1):
        """CMPZ memoria: Compara contenido de memoria con cero.
        
        Lee memoria y compara su contenido con cero actualizando flags.
        Modo: m (memoria).
        
        Parámetros
        ----------
        op1 : bytearray
            Dirección de memoria.
        """
        self._mar[:] = op1[:]
        self._read_from_ram()
        self.cmp_ra(self.int_to_bytes(0, 8), self._mdr)