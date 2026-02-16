"""Addressing helpers for the MT25Q-like 32MiB model."""

from dataclasses import dataclass

CAPACITY_BYTES = 33_554_432
MAX_ADDRESS = 0x01FF_FFFF
SECTOR_SIZE = 0x1_0000
SUB32_SIZE = 0x8000
SUB4_SIZE = 0x1000
PAGE_SIZE = 0x100
SECTORS_TOTAL = 512


@dataclass(frozen=True)
class Region:
    unit_id: int
    start: int
    end: int
    size: int


def validate_address(addr: int) -> None:
    if not (0 <= addr <= MAX_ADDRESS):
        raise ValueError(f"Address out of range: 0x{addr:X}")


def sector_region(addr: int) -> Region:
    validate_address(addr)
    sector_id = addr >> 16
    start = sector_id * SECTOR_SIZE
    return Region(sector_id, start, start + 0xFFFF, SECTOR_SIZE)


def sub32_region(addr: int) -> Region:
    validate_address(addr)
    sub32_id = addr >> 15
    start = sub32_id * SUB32_SIZE
    return Region(sub32_id, start, start + 0x7FFF, SUB32_SIZE)


def sub4_region(addr: int) -> Region:
    validate_address(addr)
    sub4_id = addr >> 12
    start = sub4_id * SUB4_SIZE
    return Region(sub4_id, start, start + 0xFFF, SUB4_SIZE)


def page_region(addr: int) -> Region:
    validate_address(addr)
    page_id = addr >> 8
    start = page_id * PAGE_SIZE
    return Region(page_id, start, start + 0xFF, PAGE_SIZE)


def sector_start(sector_id: int) -> int:
    if not 0 <= sector_id < SECTORS_TOTAL:
        raise ValueError("Invalid sector")
    return sector_id * SECTOR_SIZE


def dataset_address(sector_id: int, page_in_sector: int) -> tuple[int, int]:
    if not (0 <= sector_id < SECTORS_TOTAL):
        raise ValueError("Invalid sector")
    if not (0 <= page_in_sector < 256):
        raise ValueError("Invalid page index")
    start = sector_id * SECTOR_SIZE + page_in_sector * PAGE_SIZE
    return start, start + 0xFF
