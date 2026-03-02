from memoria.ram import ram, SP_INITIAL
from .alu import ALU
from .decoder import Decoder
from .microinstructions_mixin import MicroinstructionMixin
from .instruction_map import get_methods_map

RUNNING = 1
HALTED = 0

"""Control Unit Module
====================

Implementa la Unidad de Control del procesador Cacao Core 64.

Gestiona el flujo de ejecución de instrucciones: ciclo fetch-decode-execute,
registros del procesador, memoria (RAM), interrupciones y microinstrucciones.

Clases
------
ControlUnit : Unidad de control principal del procesador.

Constantes
----------
RUNNING : int
    Estado del procesador ejecutando instrucciones.
HALTED : int
    Estado del procesador detenido.

Ejemplo de uso:
    cu = ControlUnit()
    cu.boot(start_address=0)
    cu.run_full_exec()  # Ejecutar programa completo
"""

class ControlUnit(MicroinstructionMixin):
    """Unidad de Control del procesador Cacao Core 64.
    
    Gestiona la ejecución de instrucciones, registro de estado, memoria y
    microinstrucciones. Implementa el ciclo fetch-decode-execute y manejo
    de interrupciones.
    
    Atributos
    ---------
    state : int
        Estado actual del procesador (RUNNING o HALTED).
    INTR : bool
        Bandera de interrupción pendiente.
    INTA : bool
        Bandera de reconocimiento de interrupción.
    _registers : list[bytearray]
        16 registros de propósito general (8 bytes c/u).
    _pc : bytearray
        Program Counter (8 bytes).
    _ir : bytearray
        Instruction Register (8 bytes).
    _mar : bytearray
        Memory Address Register (4 bytes).
    _mdr : bytearray
        Memory Data Register (6 bytes).
    _fr : bytearray
        Flags Register (1 byte).
    _dp : bytearray
        Decode Pointer (1 byte).
    _alu : ALU
        Unidad Aritmético-Lógica.
    _decoder : Decoder
        Decodificador de instrucciones.
    """
    _flags_indexes = {"z":4,
                      "s":3,
                      "c":2,
                      "v":1,
                      "i":0
                      }
    _mode_length = {
        "r": 4,
        "i": 16,
        "m": 32,
        "n": 4
    }

    def __init__(self):
        """Inicializa la Unidad de Control.
        
        Crea todos los registros, la ALU y el Decodificador. El estado
        inicial es HALTED hasta que se ejecute _boot().
        """
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

        self._methods = get_methods_map(self)

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

        return values_dict


    def boot(self, start_address: int):
        """Inicializa el sistema (Power-On Reset).
        
        Limpia los flags, establece el Stack Pointer, configura el PC en la
        dirección de inicio y cambia el estado a RUNNING.
        
        Parámetros
        ----------
        start_address : int
            Dirección de memoria donde comienza el programa (típicamente 0).
        """
        #Limpiar registros
        self._fr[:] = (0).to_bytes(1, byteorder='little', signed=False)
        for reg in range(0, 16):
            self._registers[reg][:] = bytearray(8)

        #Ubicar la posición inicial de la pila
        self._registers[13][:] = SP_INITIAL.to_bytes(8, byteorder='little', signed=False)

        #Establecer el punto de partida (Dirección de la primera instrucción)
        self._pc[:] = start_address.to_bytes(8, byteorder='little')
        
        #Cambiar el estado a RUNNING
        self.state = RUNNING
        
        print(f"Sistema Re-Iniciado. PC configurado en: {start_address}")
        
    def run_full_exec(self):
        """Ejecuta el programa completo hasta que se detiene (HLT).
        
        Realiza el ciclo fetch-decode-execute repetidamente hasta que
        el procesador pasa a estado HALTED o ocurre una excepción.
        """
        try:
            while self.state == RUNNING:
                self._fetch()
                
        except Exception as e:
            print(f"Error de ejecución: {e}")
            self.state = HALTED
    
    def run_step(self):
        """Ejecuta un paso (instrucción) del programa.
        
        Realiza un ciclo fetch-decode-execute único. Útil para depuración.
        """
        if self.state == RUNNING:
            self._fetch()
    
    def _fetch(self):
        """Fase FETCH del ciclo de ejecución.
        
        Lee la instrucción desde RAM usando PC, la carga en IR, incrementa PC,
        decodifica la instrucción y la ejecuta.
        """
        self._mar[:] = self._pc[:]
        
        self._read_from_ram()

        self._ir[:] = self._mdr[:]

        acc = self._registers[15][:]
        self._alu.add(self._pc, bytearray((8).to_bytes(8, byteorder='little', signed=True)))
        self._pc[:] = self._registers[15][:]
        self._registers[15][:] = acc
        print("Completó FETCH")
        self._decode()
        
    def _decode(self):
        """Fase DECODE del ciclo de ejecución.
        
        Reinicia el Decode Pointer, decodifica la instrucción usando el
        Decodificador y extrae el nombre de la microinstrucción y sus modos.
        """
        self._dp[:] = (0).to_bytes(1, byteorder='little', signed=False)
        instruction = self._decoder.decode(self._ir)
        try:
            name, modes = instruction.split('_')
        except:
            name = instruction
            modes = []
        print("Completó DECODE")
        self._execute(name, modes)

    def _execute(self, name, modes):
        """Fase EXECUTE del ciclo de ejecución.
        
        Extrae operandos según los modos de direccionamiento y ejecuta
        la microinstrucción correspondiente.
        
        Parámetros
        ----------
        name : str
            Nombre de la microinstrucción sin modo.
        modes : str
            Modos de direccionamiento (r=registro, i=inmediato, m=memoria, n=indirecto).
        """
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
        self._methods[name+"_"+modes](ops[0], ops[1])

        self._registers[15][:] = acc[:]
        
        print("Completó EXECUTE")
        self._check_intp()
        
    def _check_intp(self):
        """Verifica y maneja interrupciones pendientes.
        
        Si hay una interrupción pendiente, guarda el estado del procesador
        en la pila y llama al manejador de interrupciones.
        """
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
        """Manejador de interrupciones.
        
        Parámetros
        ----------
        vector : int
            Vector de interrupción que identifica el tipo de interrupción.
        """
        pass

    #################################
    #   INTERACCIÓN CON MEMORIA     #
    #################################
    def _read_from_ram(self, size=8):
        """Lee datos desde RAM usando MAR en MDR.
        
        La dirección se toma de MAR y los datos se escriben en MDR.
        
        Parámetros
        ----------
        size : int, opcional
            Número de bytes a leer (default: 8).
        """
        direccion = int.from_bytes(self._mar[:], byteorder='little', signed=False)
        self._mdr[:] = ram.read(direccion, size)

    def _write_to_ram(self, size=8):
        """Escribe datos en RAM desde MDR usando dirección en MAR.
        
        Parámetros
        ----------
        size : int, opcional
            Número de bytes a escribir (default: 8).
        """
        direccion = int.from_bytes(self._mar[:], byteorder='little', signed=False)
        value = self._mdr[:size]
        ram.write(direccion, value)
    
    #################################
    #     FUNCIONES AUXILIARES      #
    #################################
    @staticmethod
    def int_to_bytes(value, size) -> bytes:
        """Convierte un entero a bytes con tamaño específico.
        
        Parámetros
        ----------
        value : int
            Valor entero a convertir.
        size : int
            Número de bits del valor.
        
        Retorna
        -------
        bytes
            Representación en bytes.
        """
        return ((value >> (64 - size)) << (64-size)).to_bytes(8, byteorder='little', signed=True)
    
    @staticmethod
    def bytes_to_int(b_array, signo=True):
        """Convierte bytes a entero.
        
        Parámetros
        ----------
        b_array : bytearray
            Array de bytes a convertir.
        signo : bool, opcional
            Si es True, interpreta como signed; si es False, unsigned (default: True).
        
        Retorna
        -------
        int
            Valor entero.
        """
        return int.from_bytes(b_array[:], byteorder='little', signed=signo)
    
    @staticmethod
    def _to_binary(register:bytearray, size, sign):
        """Convierte un registro a su representación binaria en string.
        
        Parámetros
        ----------
        register : bytearray
            Registro a convertir.
        size : int
            Tamaño en bits de la representación.
        sign : bool
            Si es True, interpreta como signed; si es False, unsigned.
        
        Retorna
        -------
        str
            String binario rellenado con ceros.
        """
        number = int.from_bytes(register, byteorder='little', signed=sign)
        return f"{number:b}".zfill(size)
    
    


if __name__ == '__main__':
    proc = ControlUnit()

    print(proc._to_binary(bytearray([2,3]), 64, False))
