from os import path
from processor.control_unit import ControlUnit
from memoria.ram import VECTOR_TABLE, SUBROUTINES, ram
from loader.cacao_loader import loader
from compiler import compiler

BASE_PATH = path.dirname(path.abspath(__file__))
VECTOR_PATH = path.join(BASE_PATH, "memoria", "system_rom", "rom_vectors.txt")
ROUTINE_PATH = path.join(BASE_PATH, "memoria", "system_rom", "rom_subroutines.txt")


class CacaoCore64:
    def __init__(self):
        self.ram_memory = ram
        self.loader = loader
        self.loader.read_and_load(VECTOR_PATH, VECTOR_TABLE, "hex")
        self.loader.read_and_load(ROUTINE_PATH, SUBROUTINES, "hex")
        self.processor = ControlUnit()
        self.compiler = compiler

    def boot(self, start_address):
        self.processor.boot(start_address)

    def run_full(self):
        self.processor.run_full_exec()

    def run_step(self):
        self.processor.run_step()
    
    def compile(self, file_addr, file_len):
        file = self.ram_memory.read(file_addr, file_len)
        data = file.replace(b'\x00', b'')
        code = data.decode('utf-8')
        return self.compiler.compile(code)


if __name__=="__main__":
    compu = CacaoCore64()
    compu.boot(0x00001000)
    compu.run_full()