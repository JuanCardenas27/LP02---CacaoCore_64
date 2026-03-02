from processor import control_unit
from memoria import ram
class CocoaCore64:
    def __init__(self):
        self.ram_memory = ram
        #self.io_entry = ¿?
        self.processor = control_unit.ControlUnit()