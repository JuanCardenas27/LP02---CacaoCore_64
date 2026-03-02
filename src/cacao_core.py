from processor.control_unit import ControlUnit
from memoria import ram

class CacaoCore64:
    def __init__(self):
        self.ram_memory = ram
        #self.io_entry = ¿?
        self.processor = ControlUnit()

    def boot(self, start_address):
        self.processor.boot(start_address)

    def run_full(self):
        self.processor.run_full_exec()

    def run_step(self):
        self.processor.run_step()
