import struct
import time
from array import array
from typing import Dict, List, Optional

from .disk import Disk, DiskError


class FileSystemError(Exception):
    """Errores del sistema de archivos."""


class SimpleFS:
    """Sistema de archivos simple con FAT y directorio fijo."""

    MAGIC = b"CACDISK1"
    VERSION = 1

    FAT_FREE = 0
    FAT_EOF = 0xFFFFFFFF
    FAT_RESERVED = 0xFFFFFFFE

    DIR_ENTRY_SIZE = 128

    SUPERBLOCK_STRUCT = struct.Struct("<8sHHIIIIII")
    DIR_ENTRY_STRUCT = struct.Struct("<BBH Q I I 108s")

    def __init__(
        self,
        disk: Disk,
        format_if_missing: bool = True,
        dir_blocks: int = 1024,
    ) -> None:
        self.disk = disk
        self.disk.open()
        self.dir_blocks = dir_blocks
        self._fat: Optional[array] = None

        if self._is_formatted():
            self._load_superblock()
            self._load_fat()
        elif format_if_missing:
            self.format()
        else:
            raise FileSystemError("Disk is not formatted")

    def format(self) -> None:
        total_blocks = self.disk.total_blocks
        fat_blocks = self._calc_fat_blocks(total_blocks)
        dir_blocks = self.dir_blocks
        data_start = 1 + fat_blocks + dir_blocks

        if data_start >= total_blocks:
            raise FileSystemError("Disk too small for metadata")

        self._superblock = {
            "block_size": self.disk.block_size,
            "total_blocks": total_blocks,
            "fat_start": 1,
            "fat_blocks": fat_blocks,
            "dir_start": 1 + fat_blocks,
            "dir_blocks": dir_blocks,
            "data_start": data_start,
        }

        self._write_superblock()

        fat = array("I", [self.FAT_FREE] * total_blocks)
        for i in range(data_start):
            fat[i] = self.FAT_RESERVED
        self._fat = fat
        self._save_fat()
        self._clear_directory()

    def list_files(self) -> List[Dict]:
        entries = []
        for index, entry in enumerate(self._iter_dir_entries()):
            if entry["in_use"]:
                entry["index"] = index
                entries.append(entry)
        return entries

    def read_file(self, name: str) -> bytes:
        entry = self._find_entry(name)
        if not entry:
            raise FileSystemError(f"File not found: {name}")
        return self._read_chain(entry["first_block"], entry["size"])

    def write_file(self, name: str, data: bytes) -> None:
        if not name:
            raise FileSystemError("File name is required")
        if len(data) == 0:
            data = b""

        existing = self._find_entry(name)
        if existing:
            self._free_chain(existing["first_block"])
            self._clear_entry(existing["index"])

        blocks_needed = max(1, (len(data) + self.disk.block_size - 1) // self.disk.block_size)
        blocks = self._alloc_blocks(blocks_needed)
        self._write_chain(blocks, data)

        entry = {
            "in_use": 1,
            "type": 1,
            "size": len(data),
            "first_block": blocks[0],
            "mtime": int(time.time()),
            "name": name,
        }
        self._write_entry(entry)
        self._save_fat()

    def delete_file(self, name: str) -> None:
        entry = self._find_entry(name)
        if not entry:
            raise FileSystemError(f"File not found: {name}")
        self._free_chain(entry["first_block"])
        self._clear_entry(entry["index"])
        self._save_fat()

    def flush(self) -> None:
        self._save_fat()
        self.disk.flush()

    def _is_formatted(self) -> bool:
        try:
            block0 = self.disk.read_block(0)
        except DiskError:
            return False
        magic = block0[: len(self.MAGIC)]
        return magic == self.MAGIC

    def _load_superblock(self) -> None:
        block0 = self.disk.read_block(0)
        values = self.SUPERBLOCK_STRUCT.unpack(block0[: self.SUPERBLOCK_STRUCT.size])
        magic, version, block_size, total_blocks, fat_start, fat_blocks, dir_start, dir_blocks, data_start = values
        if magic != self.MAGIC or version != self.VERSION:
            raise FileSystemError("Invalid disk format")
        if block_size != self.disk.block_size or total_blocks != self.disk.total_blocks:
            raise FileSystemError("Disk geometry mismatch")
        self._superblock = {
            "block_size": block_size,
            "total_blocks": total_blocks,
            "fat_start": fat_start,
            "fat_blocks": fat_blocks,
            "dir_start": dir_start,
            "dir_blocks": dir_blocks,
            "data_start": data_start,
        }

    def _write_superblock(self) -> None:
        sb = self._superblock
        header = self.SUPERBLOCK_STRUCT.pack(
            self.MAGIC,
            self.VERSION,
            sb["block_size"],
            sb["total_blocks"],
            sb["fat_start"],
            sb["fat_blocks"],
            sb["dir_start"],
            sb["dir_blocks"],
            sb["data_start"],
        )
        padding = bytes(self.disk.block_size - len(header))
        self.disk.write_block(0, header + padding)

    def _calc_fat_blocks(self, total_blocks: int) -> int:
        bytes_needed = total_blocks * 4
        block_size = self.disk.block_size
        return (bytes_needed + block_size - 1) // block_size

    def _load_fat(self) -> None:
        sb = self._superblock
        raw = bytearray()
        for i in range(sb["fat_blocks"]):
            raw.extend(self.disk.read_block(sb["fat_start"] + i))
        fat = array("I")
        fat.frombytes(raw)
        self._fat = fat[: sb["total_blocks"]]

    def _save_fat(self) -> None:
        if self._fat is None:
            return
        sb = self._superblock
        raw = self._fat.tobytes()
        total_bytes = sb["fat_blocks"] * self.disk.block_size
        raw = raw[:total_bytes].ljust(total_bytes, b"\0")
        for i in range(sb["fat_blocks"]):
            start = i * self.disk.block_size
            end = start + self.disk.block_size
            self.disk.write_block(sb["fat_start"] + i, raw[start:end])

    def _clear_directory(self) -> None:
        sb = self._superblock
        empty = bytes(self.disk.block_size)
        for i in range(sb["dir_blocks"]):
            self.disk.write_block(sb["dir_start"] + i, empty)

    def _iter_dir_entries(self):
        sb = self._superblock
        total_entries = (sb["dir_blocks"] * self.disk.block_size) // self.DIR_ENTRY_SIZE
        for index in range(total_entries):
            entry = self._read_entry(index)
            entry["index"] = index
            yield entry

    def _read_entry(self, index: int) -> Dict:
        sb = self._superblock
        entries_per_block = self.disk.block_size // self.DIR_ENTRY_SIZE
        block_index = sb["dir_start"] + (index // entries_per_block)
        offset = (index % entries_per_block) * self.DIR_ENTRY_SIZE
        block = self.disk.read_block(block_index)
        entry_raw = block[offset:offset + self.DIR_ENTRY_SIZE]
        in_use, ftype, _res, size, first_block, mtime, name_raw = self.DIR_ENTRY_STRUCT.unpack(entry_raw)
        name = name_raw.split(b"\0", 1)[0].decode("utf-8", errors="ignore")
        return {
            "in_use": in_use,
            "type": ftype,
            "size": size,
            "first_block": first_block,
            "mtime": mtime,
            "name": name,
        }

    def _write_entry(self, entry: Dict) -> None:
        index = entry.get("index")
        if index is None:
            index = self._find_free_entry_index()
        if index is None:
            raise FileSystemError("Directory full")

        name_bytes = entry["name"].encode("utf-8")
        if len(name_bytes) >= 108:
            raise FileSystemError("File name too long")
        name_raw = name_bytes.ljust(108, b"\0")

        packed = self.DIR_ENTRY_STRUCT.pack(
            int(entry.get("in_use", 1)),
            int(entry.get("type", 1)),
            0,
            int(entry.get("size", 0)),
            int(entry.get("first_block", 0)),
            int(entry.get("mtime", 0)),
            name_raw,
        )

        sb = self._superblock
        entries_per_block = self.disk.block_size // self.DIR_ENTRY_SIZE
        block_index = sb["dir_start"] + (index // entries_per_block)
        offset = (index % entries_per_block) * self.DIR_ENTRY_SIZE
        block = bytearray(self.disk.read_block(block_index))
        block[offset:offset + self.DIR_ENTRY_SIZE] = packed
        self.disk.write_block(block_index, bytes(block))

    def _clear_entry(self, index: int) -> None:
        sb = self._superblock
        entries_per_block = self.disk.block_size // self.DIR_ENTRY_SIZE
        block_index = sb["dir_start"] + (index // entries_per_block)
        offset = (index % entries_per_block) * self.DIR_ENTRY_SIZE
        block = bytearray(self.disk.read_block(block_index))
        block[offset:offset + self.DIR_ENTRY_SIZE] = bytes(self.DIR_ENTRY_SIZE)
        self.disk.write_block(block_index, bytes(block))

    def _find_free_entry_index(self) -> Optional[int]:
        sb = self._superblock
        total_entries = (sb["dir_blocks"] * self.disk.block_size) // self.DIR_ENTRY_SIZE
        for index in range(total_entries):
            entry = self._read_entry(index)
            if not entry["in_use"]:
                return index
        return None

    def _find_entry(self, name: str) -> Optional[Dict]:
        for entry in self._iter_dir_entries():
            if entry["in_use"] and entry["name"] == name:
                return entry
        return None

    def _alloc_blocks(self, count: int) -> List[int]:
        if self._fat is None:
            raise FileSystemError("FAT not loaded")
        sb = self._superblock
        blocks = []
        for index in range(sb["data_start"], sb["total_blocks"]):
            if self._fat[index] == self.FAT_FREE:
                blocks.append(index)
                if len(blocks) == count:
                    break
        if len(blocks) != count:
            raise FileSystemError("Disk full")

        for i in range(count - 1):
            self._fat[blocks[i]] = blocks[i + 1]
        self._fat[blocks[-1]] = self.FAT_EOF
        return blocks

    def _free_chain(self, start_block: int) -> None:
        if self._fat is None:
            return
        current = start_block
        sb = self._superblock
        while current not in (self.FAT_EOF, self.FAT_FREE, self.FAT_RESERVED):
            next_block = self._fat[current]
            self._fat[current] = self.FAT_FREE
            current = next_block
            if current < sb["data_start"]:
                break

    def _write_chain(self, blocks: List[int], data: bytes) -> None:
        block_size = self.disk.block_size
        for i, block_index in enumerate(blocks):
            start = i * block_size
            end = start + block_size
            chunk = data[start:end]
            if len(chunk) < block_size:
                chunk = chunk.ljust(block_size, b"\0")
            self.disk.write_block(block_index, chunk)

    def _read_chain(self, start_block: int, size: int) -> bytes:
        if self._fat is None:
            raise FileSystemError("FAT not loaded")
        block_size = self.disk.block_size
        data = bytearray()
        current = start_block
        sb = self._superblock
        while current not in (self.FAT_EOF, self.FAT_FREE, self.FAT_RESERVED):
            data.extend(self.disk.read_block(current))
            current = self._fat[current]
            if current < sb["data_start"]:
                break
        return bytes(data[:size])
