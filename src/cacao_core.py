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
        self.processor = ControlUnit()
        self.compiler = compiler

        # Inicializar disco y sistema de archivos primero
        self.disk = Disk(DISK_PATH, DISK_SIZE_BYTES, DISK_BLOCK_SIZE)
        self.fs = SimpleFS(self.disk)

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

        # Cargar ROM desde disco; si faltan, mostrar mensaje claro y abrir Disk Editor
        try:
            vectors_text = _fs_read_text('/system/rom_vectors.txt')
            self.loader.load_to_ram(vectors_text.splitlines(), VECTOR_TABLE, "hex")

            routines_text = _fs_read_text('/system/rom_subroutines.txt')
            self.loader.load_to_ram(routines_text.splitlines(), SUBROUTINES, "hex")

        except FileNotFoundError as e:
            # Mensaje claro en consola
            print(f"ERROR: {e}\nLa imagen de disco no contiene las ROMs requeridas.")
            # Intentar abrir el editor de disco para inicializar imagen
            try:
                import tkinter as tk
                from disco.cacao_disk_editor import CacaoDiskEditor

                editor = CacaoDiskEditor()
                # Proveer disco y FS al editor
                editor.disk = self.disk
                editor.fs = self.fs
                # Inicializar variables mínimas usadas por la UI
                editor.filename_var = tk.StringVar()
                editor._zoom_manager = None
                editor._palette_name = getattr(editor, '_palette_name', 'default')
                editor._build_ui()
                editor.mainloop()
            except Exception as ex:
                raise RuntimeError(
                    f"ROM files missing and unable to launch Disk Editor: {ex}"
                ) from e

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