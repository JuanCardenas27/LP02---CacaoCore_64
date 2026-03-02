from memoria.ram import ram, SP_INITIAL, VECTOR_TABLE
from alu import ALU
from decoder import Decoder

RUNNING = 1
HALTED = 0

class ControlUnit:
    _flags_indexes = {"z":4,
                      "s":3,
                      "c":2,
                      "v":1,
                      "i":0
                      }
    _methods = {} # nombre (sin modo) : lambda x,y: self.name(x, [y])
    _mode_length = {
        "r": 4,
        "i": 16,
        "m": 32,
        "n": 4
    }

    def __init__(self):
        self.state = HALTED
        self.INTR = False
        self.INTA = False

        self._registers =[
            bytearray(8) for _ in range(0, 16)
        ]

        self._pc = bytearray(8)
        self._ir = bytearray(8)
        self._mar = bytearray(4)
        self._mdr = bytearray(6)
        self._fr = bytearray(1)
        self._dp = bytearray(1)

        self._alu = ALU(self._registers[15], self._fr)
        self._decoder = Decoder(self._dp)
        self._to_binary

    def get_registers(self):
        values_dict = {}

        for i, bytea in enumerate(self._registers[:13]):
            values_dict[f"r{i}"] = self.bytes_to_int(bytea, True)
        
        values_dict["sp"] = self.bytes_to_int(self._registers[13])
        values_dict["lr"] = self.bytes_to_int(self._registers[14])
        values_dict["acc"] = self.bytes_to_int(self._registers[15])
        values_dict["pc"] = self.bytes_to_int(self._pc)
        values_dict["ir"] = self.bytes_to_int(self._ir)
        values_dict["mar"] = self.bytes_to_int(self._mar)
        values_dict["mdr"] = self.bytes_to_int(self._mdr)
        values_dict["fr"] = self.bytes_to_int(self._fr)
        values_dict["dp"] = self.bytes_to_int(self._dp)


    def boot(self, start_address: int):
        """
        Inicializa el sistema. 
        Equivale al 'Power-On Reset'.
        """
        #Limpiar registro de flags
        self._fr[:] = (0).to_bytes(8, byteorder='little', signed=False)

        #Ubicar la posición inicial de la pila
        self._registers[13][:] = SP_INITIAL.to_bytes(8, byteorder='little', signed=False)

        #Establecer el punto de partida (Dirección de la primera instrucción)
        self._pc[:] = start_address.to_bytes(8, byteorder='little')
        
        #Cambiar el estado a RUNNING
        self.state = RUNNING
        
        print(f"Sistema Re-Iniciado. PC configurado en: {start_address}")

    def run_full_exec(self):
        try:
            while self.state == RUNNING:
                self._fetch()
                
        except Exception as e:
            print(f"Error de ejecución: {e}")
            self.state = HALTED
    
    def run_step(self):
        if self.state == RUNNING:
            self._fetch()
    
    def _fetch(self):

        self._mar[:] = self._pc[:]
        
        self._read_from_ram()

        self._ir[:] = self._mdr[:]

        acc = self._registers[15]
        self._alu.add(self._pc, bytearray((8).to_bytes(8, byteorder='little', signed=True)))
        self._pc[:] = self._registers[15][:]
        self._registers[15][:] = acc[:]

        self._decode()
        
    def _decode(self):
        self._dp[:] = (0).to_bytes(1, byteorder='little', signed=False)
        instruction = self._decoder.decode(self._ir)
        try:
            name, modes = instruction.split('_')
        except:
            name = instruction
            modes = []
    
        self._execute(name, modes)

    def _execute(self, name, modes):

        ops = [bytearray() for _ in range(2)]

        for i, mode in enumerate(modes):
            initial_pos = int.from_bytes(self._dp, byteorder='little', signed=False) * 4
            final_pos = initial_pos + self._mode_length[mode]
            cod_i = self._to_binary(self._ir, 64, False)[initial_pos: final_pos + 1]

            if mode == "r":
                ops[i] = self._registers[int(cod_i, 2)]

            elif mode == "i":
                ops[i] = bytearray(int(cod_i, 2).to_bytes(8, byteorder='little', signed=True)) # ¿2 u 8 bytes?
            
            elif mode == "m":
                ops[i] = bytearray(int(cod_i, 2).to_bytes(8, byteorder='little', signed=True)) # ¿Por qué no int?
            
            elif mode == "n": # ¿Por qué no int?^^
                self._mar[:] = self._registers[int(cod_i, 2)]
                ops[i] = self._mdr[:]

        acc = self._registers[15]

        self._methods[name](ops[0], ops[1])

        self._registers[15][:] = acc[:]
        
        self._check_intp()
        
    def _check_intp(self):
        if self.INTR == True:
            self.push(self._pc)
            self.push(self._fr)
            for reg in self._registers:
                self.push(reg)
            self.INTA = True
            #TODO Pedir al controlador de int el vector
            vector = self.bytes_to_int(self._mdr)
            self._interruption_handler(vector)
            
                
    def _interruption_handler(self, vector):
        pass

    #################################
    #   INTERACCIÓN CON MEMORIA     #
    #################################
    def _read_from_ram(self, size=8):
        direccion = int.from_bytes(self._mar[:], byteorder='little', signed=False)
        self._mdr[:] = ram.read(direccion, size)

    def _write_to_ram(self, size=8):
        direccion = int.from_bytes(self._mar[:], byteorder='little', signed=False)
        value = self._mdr[:size]
        ram.write(direccion, value)
    
    #################################
    #     FUNCIONES AUXILIARES      #
    #################################
    @staticmethod
    def int_to_bytes(value, size) -> bytes:
        return ((value >> (64 - size)) << (64-size)).to_bytes(8, byteorder='little', signed=True)
    
    @staticmethod
    def bytes_to_int(b_array, signo=True):
        return int.from_bytes(b_array[:], byteorder='little', signed=signo)
    
    @staticmethod
    def _to_binary(register:bytearray, size, sign):
        number = int.from_bytes(register, byteorder='little', signed=sign)
        return f"{number:b}".zfill(size)
    
    #################################
    #       MICROINSTRUCCIONES      #
    #################################

    def hlt(self):
        self.state = HALTED
    
    def mov_ra(self, op1, op2, size):
        """Sirve para direccionamientos rr y ri"""
        value = self.bytes_to_int(op2)
        op1[:] = self.int_to_bytes(value, size)

    def mov_rm(self, op1, op2, size):
        self._mar[:]=op2[:]
        self._read_from_ram(size=size//8)
        value = self.bytes_to_int(self._mdr)
        op1[:] = self.int_to_bytes(value, size)

    def mov_ma(self, op1, op2, size):
        """Sirve para direccionamientos mr y mi"""
        value = self.bytes_to_int(op2)
        self._mdr[:] = self.int_to_bytes(value, size)
        self._mar[:] = op1[:]
        self._write_to_ram(size=size//8)

    def load_m(self, op1, size):
        self._mar[:] = op1[:]
        self._read_from_ram(size=size//8)
        value = self.bytes_to_int(self._mdr)
        self._registers[15][:] = self.int_to_bytes(value, size)
    
    def load_i(self, op1, size):
        value = self.bytes_to_int(op1)
        self._registers[15][:] = self.int_to_bytes(value, size)

    def load_rm(self, op1, op2, size):
        self._mar[:] = op2[:]
        self._read_from_ram(size=size//8)
        value = self.bytes_to_int(self._mdr)
        op1[:] = self.int_to_bytes(value, size)

    def load_ri(self, op1, op2, size):
        value = self.bytes_to_int(op2)
        op1[:] = self.int_to_bytes(value, size)
    
    def store_m(self, op1, size):
        value = self.bytes_to_int(self._registers[15])
        self._mdr[:] = self.int_to_bytes(value, size)
        self._mar[:] = op1[:]
        self._write_to_ram(size=size//8)
    
    def store_r(self, op1, size):
        value = self.bytes_to_int(self._registers[15])
        op1[:] = self.int_to_bytes(value, size)

    def store_ma(self, op1, op2, size):
        """Sirve para direccionamientos mr y mi"""
        value = self.bytes_to_int(op2)
        self._mdr[:] = self.int_to_bytes(value, size)
        self._mar[:] = op1[:]
        self._write_to_ram(size=size//8)

    def jmp(self, op1):
        self._pc = op1[:]
    
    def j_condicional(self, op1, flag):
        index = self._flags_indexes[flag]
        flags = self._to_binary(self._fr, 8, False)
        if int(flags[index]):
            self._pc = op1[:]

    def jn_condicional(self, op1, flag):
        index = self._flags_indexes[flag]
        flags = self._to_binary(self._fr, 8, False)
        if not int(flags[index]):
            self._pc = op1[:]

    def j_comparacion(self, op1, flag1, flag2, cmp):
        pass

    def call_m(self, op1):
        self._registers[14][:] = self._pc[:]
        self.push(op1)
        self.jmp(op1)
    
    def ret(self):
        """Return from subroutine using pop: update LR and PC."""
        self.pop(self._registers[14])
        self._pc[:] = self._registers[14][:]
    
    def push(self, op1):
        self._mar[:] = self._registers[13][:]
        self._mdr[:] = op1[:]
        self._write_to_ram()
        head_sp = self.bytes_to_int(self._registers[13], False)
        head_sp -= 8
        self._registers[13][:] = self.int_to_bytes(head_sp, 64)
    
    def pop(self, op1):
        self._mar[:] = self._registers[13][:]
        self._read_from_ram()
        op1[:] = self._mdr[:]
        head_sp = self.bytes_to_int(self._registers[13], False)
        head_sp += 8
        self._registers[13][:] = self.int_to_bytes(head_sp, 64)
    
    def iret(self):
        for reg in range(15,0, -1):
            self.pop(self._registers[reg])
        self.pop(self._fr)
        self.pop(self._pc)
    
    def int(self):
        pass

    def nop(self):
        pass
    
    def ei(self):
        """Enable interrupts by setting flag bit0."""
        flags = int.from_bytes(self._fr, byteorder='little', signed=False)
        flags |= 1
        self._fr[:] = flags.to_bytes(1, byteorder='little', signed=False)

    def di(self):
        """Disable interrupts by clearing flag bit0."""
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
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.add(self._registers[15], self._mdr)

    def add_a(self, op1):
        """Sirve para direccionamientos r e i"""
        self._alu.add(self._registers[15], op1)

    def add_ra(self, op1, op2):
        """Sirve para direccionamientos rr e ri"""
        self._alu.add(op1, op2)
        op1[:] = self._registers[15][:]
    
    def add_rm(self, op1, op2):
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.add(op1, self._mdr)
        op1[:] = self._registers[15][:]


    def sub_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.sub(self._registers[15], self._mdr)

    def sub_a(self, op1):
        """Sirve para direccionamientos r e i"""
        self._alu.sub(self._registers[15], op1)

    def sub_ra(self, op1, op2):
        """Sirve para direccionamientos rr e ri"""
        self._alu.sub(op1, op2)
        op1[:] = self._registers[15][:]
    
    def sub_rm(self, op1, op2):
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.sub(op1, self._mdr)
        op1[:] = self._registers[15][:]

    
    def mul_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.mul(self._registers[15], self._mdr)

    def mul_a(self, op1):
        """Sirve para direccionamientos r e i"""
        self._alu.mul(self._registers[15], op1)

    def mul_ra(self, op1, op2):
        """Sirve para direccionamientos rr e ri"""
        self._alu.mul(op1, op2)
        op1[:] = self._registers[15][:]
    
    def mul_rm(self, op1, op2):
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.mul(op1, self._mdr)
        op1[:] = self._registers[15][:]

    
    def div_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.div(self._registers[15], self._mdr)

    def div_a(self, op1):
        """Sirve para direccionamientos r e i"""
        self._alu.div(self._registers[15], op1)

    def div_ra(self, op1, op2):
        """Sirve para direccionamientos rr e ri"""
        self._alu.div(op1, op2)
        op1[:] = self._registers[15][:]
    
    def div_rm(self, op1, op2):
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.div(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def inc_r(self, op1):
        self._alu.inc(op1)

    def inc_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.inc(self._mdr)

    def dec_r(self, op1):
        self._alu.dec(op1)

    def dec_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.dec(self._mdr)

    def and_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.and_a(self._registers[15], self._mdr)

    def and_a(self, op1):
        """Sirve para direccionamientos r e i"""
        self._alu.and_a(self._registers[15], op1)

    def and_ra(self, op1, op2):
        """Sirve para direccionamientos rr e ri"""
        self._alu.and_a(op1, op2)
        op1[:] = self._registers[15][:]
    
    def and_rm(self, op1, op2):
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.and_a(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def or_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.or_a(self._registers[15], self._mdr)

    def or_a(self, op1):
        """Sirve para direccionamientos r e i"""
        self._alu.or_a(self._registers[15], op1)

    def or_ra(self, op1, op2):
        """Sirve para direccionamientos rr e ri"""
        self._alu.or_a(op1, op2)
        op1[:] = self._registers[15][:]
    
    def or_rm(self, op1, op2):
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.or_a(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def xor_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.xor_a(self._registers[15], self._mdr)

    def xor_a(self, op1):
        """Sirve para direccionamientos r e i"""
        self._alu.xor_a(self._registers[15], op1)

    def xor_ra(self, op1, op2):
        """Sirve para direccionamientos rr e ri"""
        self._alu.xor_a(op1, op2)
        op1[:] = self._registers[15][:]
    
    def xor_rm(self, op1, op2):
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.xor_a(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def not_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.not_a(self._mdr)

    def not_r(self, op1):
        self._alu.not_a(op1)

    def cmp_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.cmp(self._registers[15], self._mdr)

    def cmp_a(self, op1):
        """Sirve para direccionamientos r e i"""
        self._alu.cmp(self._registers[15], op1)

    def cmp_ra(self, op1, op2):
        """Sirve para direccionamientos rr e ri"""
        self._alu.cmp(op1, op2)
        op1[:] = self._registers[15][:]
    
    def cmp_rm(self, op1, op2):
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.cmp(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def test_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self._alu.test(self._registers[15], self._mdr)

    def test_a(self, op1):
        """Sirve para direccionamientos r e i"""
        self._alu.test(self._registers[15], op1)

    def test_ra(self, op1, op2):
        """Sirve para direccionamientos rr e ri"""
        self._alu.test(op1, op2)
        op1[:] = self._registers[15][:]
    
    def test_rm(self, op1, op2):
        self._mar[:] = op2[:]
        self._read_from_ram()
        self._alu.test(op1, self._mdr)
        op1[:] = self._registers[15][:]

    def shl_i(self, op1):
        self._alu.shl(op1)

    def shl_ri(self, op1, op2):
        self.load_i(op1, 8)
        self._alu.shl(op2)
        op1[:] = self._registers[15][:]

    def shr_i(self, op1):
        self._alu.shr(op1)

    def shr_ri(self, op1, op2):
        self.load_i(op1, 8)
        self._alu.shr(op2)
        op1[:] = self._registers[15][:]

    def swap_r(self, op1):
        temp = op1[:]
        op1[:] = self._registers[15][:]
        self._registers[15][:] = temp

    def swap_rr(self, op1, op2):
        temp = op1[:]
        op1[:] = op2[:]
        op2[:] = temp

    def lea_m(self, op1):
        self.load_i(op1, 32)

    def lea_rm(self, op1, op2):
        self.load_i(op2, 32)
        op1[:] = self._registers[15][:]

    def ror_i(self, op1):
        value = self.bytes_to_int(self._registers[15])
        shift = self.bytes_to_int(op1)
        tmp = (value >> shift) | ((value << (8 - shift)) & (2**8 - 1))
        self._registers[15][:] = self.int_to_bytes(tmp, 64)
    
    def ror_ri(self, op1, op2):
        value = self.bytes_to_int(op1)
        shift = self.bytes_to_int(op2)
        op1[:] = (value >> shift) | ((value << (8 - shift)) & (2**8 - 1))

    def cmpz_r(self, op1):
        self.cmp_ra(self.int_to_bytes(0, 8), op1)

    def cmpz_m(self, op1):
        self._mar[:] = op1[:]
        self._read_from_ram()
        self.cmp_ra(self.int_to_bytes(0, 8), self._mdr)
    
    

    
    
    


if __name__ == '__main__':
    proc = ControlUnit()
    print(proc._to_binary(bytearray([2,3]), 64, False))
