from memoria.ram import ram
from alu import ALU
from decoder import Decoder

RUNNING = 1
HALTED = 0

class ControlUnit:

    _methods = {} # nombre (sin modo) : lambda x,y: self.name(x, [y])
    _mode_length = {
        "r": 4,
        "i": 16,
        "m": 32,
        "n": 4
    }

    def __init__(self):
        self.state = HALTED

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

    def _boot(self, start_address: int):
        """
        Inicializa el sistema. 
        Equivale al 'Power-On Reset'.
        """
        #Limpiar registro de flags
        self._fr[:] = (0).to_bytes(8, byteorder='little', signed=False)

        #Establecer el punto de partida (Dirección de la primera instrucción)
        self._pc[:] = start_address.to_bytes(8, byteorder='little')
        
        #Cambiar el estado a RUNNING
        self.state = RUNNING
        
        print(f"Sistema Re-Iniciado. PC configurado en: {start_address}")
        
    def _run_full_exec(self):
        try:
            while self.state == RUNNING:
                self._fetch()
                
        except Exception as e:
            print(f"Error de ejecución: {e}")
            self.state = HALTED
    
    def _run_step(self):
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
                ops[i] = bytearray(int(cod_i, 2).to_bytes(2, byteorder='little', signed=True)) # ¿2 u 8 bytes?
            
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
        # if ControlBus.INTR == ON:
        #     while ControlBus.INTR == OFF:
                pass

    #################################
    #   INTERACCIÓN CON MEMORIA     #
    #################################
    def _read_from_ram(self):
        direccion = int.from_bytes(self._mar[:], byteorder='little', signed=False)
        self._mdr[:] = ram.read_word(direccion).to_bytes(8, byteorder='little', signed=False)

    def _write_to_ram(self):
        direccion = int.from_bytes(self._mar[:], byteorder='little', signed=False)
        value = int.from_bytes(self._mdr[:], byteorder='little', signed=False)
        ram.write_word(direccion, value)
    
    #################################
    #     FUNCIONES AUXILIARES      #
    #################################
    @staticmethod
    def int_to_bytes(value, size) -> bytes:
        return ((value >> (64 - size)) << (64-size)).to_bytes(8, byteorder='little', signed=True)
    
    @staticmethod
    def bytes_to_int(b_array):
        return int.from_bytes(b_array[:], byteorder='little', signed=True)
    
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
        self._mar=op2[:]
        self._read_from_ram()
        value = self.bytes_to_int(self._mdr)
        op1[:] = self.int_to_bytes(value, size)

    def mov_ma(self, op1, op2, size):
        """Sirve para direccionamientos rr y ri"""
        value = self.bytes_to_int(op2)
        self._mdr[:] = self.int_to_bytes(value, size)
        self._mar[:] = op1[:]
        self._write_to_ram()

    def load_m(self, op1, size):
        self._mar[:] = op1[:]
        self._read_from_ram()
        value = self.bytes_to_int(self._mdr)
        self._registers[15][:] = self.int_to_bytes(value, size)
    
    def load_i(self, op1, size):
        value = self.bytes_to_int(op1)
        self._registers[15][:] = self.int_to_bytes(value, size)

    def load_rm(self, op1, op2, size):
        self._mar[:] = op2[:]
        self._read_from_ram()
        value = self.bytes_to_int(self._mdr)
        op1[:] = self.int_to_bytes(value, size)

    def load_ri(self, op1, op2, size):
        value = self.bytes_to_int(op2)
        op1[:] = self.int_to_bytes(value, size)
    
    def store_m(self, op1, size):
        value = self.bytes_to_int(self._registers[15])
        self._mdr[:] = self.int_to_bytes(value, size)
        self._mar[:] = op1[:]
        self._write_to_ram()



    
    

    
    
    


if __name__ == '__main__':
    proc = ControlUnit()
    print(proc._to_binary(bytearray([2,3]), 64, False))
