import os


class DiskError(Exception):
    """Errores del disco persistente."""


def _ensure_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


class Disk:
    """Disco persistente basado en archivo binario fijo."""

    def __init__(self, path: str, size_bytes: int, block_size: int = 512) -> None:
        if size_bytes <= 0:
            raise DiskError("Disk size must be > 0")
        if block_size <= 0:
            raise DiskError("Block size must be > 0")
        if size_bytes % block_size != 0:
            raise DiskError("Disk size must be multiple of block size")

        self.path = path
        self.size_bytes = size_bytes
        self.block_size = block_size
        self.total_blocks = size_bytes // block_size
        self._fh = None

    def open(self) -> None:
        if self._fh:
            return
        _ensure_dir(self.path)
        if not os.path.exists(self.path):
            with open(self.path, "wb") as f:
                f.truncate(self.size_bytes)
        else:
            current_size = os.path.getsize(self.path)
            if current_size != self.size_bytes:
                raise DiskError(
                    f"Disk size mismatch: expected {self.size_bytes}, got {current_size}"
                )
        self._fh = open(self.path, "r+b")

    def close(self) -> None:
        if not self._fh:
            return
        self._fh.close()
        self._fh = None

    def flush(self) -> None:
        if self._fh:
            self._fh.flush()

    def read_block(self, block_index: int) -> bytes:
        self._ensure_open()
        self._check_block_index(block_index)
        self._fh.seek(block_index * self.block_size)
        data = self._fh.read(self.block_size)
        if len(data) != self.block_size:
            raise DiskError("Short read from disk")
        return data

    def write_block(self, block_index: int, data: bytes) -> None:
        self._ensure_open()
        self._check_block_index(block_index)
        if len(data) != self.block_size:
            raise DiskError("Block write must match block size")
        self._fh.seek(block_index * self.block_size)
        self._fh.write(data)

    def _ensure_open(self) -> None:
        if not self._fh:
            self.open()

    def _check_block_index(self, block_index: int) -> None:
        if block_index < 0 or block_index >= self.total_blocks:
            raise DiskError(f"Block index out of range: {block_index}")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
