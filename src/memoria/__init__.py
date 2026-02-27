# src/memoria/__init__.py
from .ram import (
    RAM, ram,
    RAM_SIZE, WORD_SIZE,
    SYS_START,   SYS_END,
    CODE_START,  CODE_END,
    DATA_START,  DATA_END,
    HEAP_START,  HEAP_END,
    STACK_START, STACK_END,
    SP_INITIAL,  PC_INITIAL,
    RAMError, AddressOutOfRange, AlignmentError,
    WriteProtectionError, InvalidSizeError,
)

__all__ = [
    "RAM", "ram",
    "RAM_SIZE", "WORD_SIZE",
    "SYS_START", "SYS_END",
    "CODE_START", "CODE_END",
    "DATA_START", "DATA_END",
    "HEAP_START", "HEAP_END",
    "STACK_START", "STACK_END",
    "SP_INITIAL", "PC_INITIAL",
    "RAMError", "AddressOutOfRange", "AlignmentError",
    "WriteProtectionError", "InvalidSizeError",
]
