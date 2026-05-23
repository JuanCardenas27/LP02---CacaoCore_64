import os
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


def _init_roms_from_host(fs):
    """Copia ROMs del host al disco simulado (primera ejecución)."""
    try:
        # Verificar si ROMs ya existen en disco
        try:
            fs.read_file("system/rom_vectors.txt")
            fs.read_file("system/rom_subroutines.txt")
            return True  # Ya existen
        except Exception:
            pass
        
        # Copiar desde host si existen
        if not (path.isfile(VECTOR_PATH) and path.isfile(ROUTINE_PATH)):
            return False
        
        print("[INFO] Inicializando ROMs en disco desde host...")
        with open(VECTOR_PATH, 'r') as f:
            vectors_data = f.read()
        with open(ROUTINE_PATH, 'r') as f:
            routines_data = f.read()
        
        fs.write_file("system/rom_vectors.txt", vectors_data.encode())
        fs.write_file("system/rom_subroutines.txt", routines_data.encode())
        fs.flush()
        
        print("[INFO] ROMs copiadas a disco exitosamente")
        return True
    except Exception as e:
        print(f"[WARN] No se pudieron copiar ROMs: {e}")
        return False


class CacaoCore64:
    def __init__(self):
        self.ram_memory = ram
        self.loader = loader_txt
        self.processor = ControlUnit()
        self.compiler = compiler

        # Inicializar disco y sistema de archivos primero
        self.disk = Disk(DISK_PATH, DISK_SIZE_BYTES, DISK_BLOCK_SIZE)
        self.fs = SimpleFS(self.disk)

        # Crear directorio storage si no existe
        storage_dir = path.dirname(DISK_PATH)
        os.makedirs(storage_dir, exist_ok=True)

        # Intentar copiar ROMs desde host en primera ejecución
        _init_roms_from_host(self.fs)

        # Helper para leer texto desde el FS (prueba con y sin '/')
        def _fs_read_text(p: str) -> str:
            candidates = [p.lstrip('/'), p]
            for c in candidates:
                try:
                    raw = self.fs.read_file(c)
                except Exception:
                    continue
                try:
                    return raw.decode('utf-8-sig')
                except Exception:
                    return raw.decode('utf-8', errors='replace')
            raise FileNotFoundError(f"Required ROM file not found on disk: {p}")

        # Cargar ROM desde disco
        try:
            vectors_text = _fs_read_text('/system/rom_vectors.txt')
            self.loader.load_to_ram(vectors_text.splitlines(), VECTOR_TABLE, "hex")

            routines_text = _fs_read_text('/system/rom_subroutines.txt')
            self.loader.load_to_ram(routines_text.splitlines(), SUBROUTINES, "hex")

        except FileNotFoundError as e:
            print(f"\n✗ ERROR CRÍTICO: {e}")
            print("  Las ROMs no están disponibles en disco ni en el host.")
            print("\n  SOLUCIÓN:")
            print("  1. Verificar que existen:")
            print(f"     - {VECTOR_PATH}")
            print(f"     - {ROUTINE_PATH}")
            print("  2. O inicializar manualmente con Disk Editor (CACAO_DEV_MODE=1)")
            raise RuntimeError(f"ROM initialization failed: {e}") from e

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