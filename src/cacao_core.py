from os import path
from processor.control_unit import ControlUnit, RUNNING
from memoria.ram import VECTOR_TABLE, SUBROUTINES, ram
from enlazador_cargador.loader_txt import loader_txt
from compiler import compiler
from disco.disk import Disk
from disco.simple_fs import SimpleFS

BASE_PATH = path.dirname(path.abspath(__file__))
VECTOR_PATH = path.join(BASE_PATH, "memoria", "system_rom", "rom_vectors.txt")
ROUTINE_PATH = path.join(BASE_PATH, "memoria", "system_rom", "rom_subroutines.txt")
DISK_PATH = path.abspath(path.join(BASE_PATH, "..", "storage", "cacao_disk.img"))
DISK_SIZE_BYTES = 512 * 1024 * 1024
DISK_BLOCK_SIZE = 512


class CacaoCore64:
    def __init__(self):
        self.ram_memory = ram
        self.loader = loader_txt
        self.loader.read_and_load(VECTOR_PATH, VECTOR_TABLE, "hex")
        self.loader.read_and_load(ROUTINE_PATH, SUBROUTINES, "hex")
        self.processor = ControlUnit()
        self.compiler = compiler
        self.disk = Disk(DISK_PATH, DISK_SIZE_BYTES, DISK_BLOCK_SIZE)
        self.fs = SimpleFS(self.disk)

    def boot(self, start_address):
        self.processor.boot(start_address)

    def run_full(self):
        self.processor.run_full_exec()

    def run_step(self):
        self.processor.run_step()


if __name__=="__main__":
    compu = CacaoCore64()
    compu.boot(0x00001000)
    compu.run_full()