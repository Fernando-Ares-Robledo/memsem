from __future__ import annotations

from dataclasses import dataclass

PAPER_WORD_BYTES = 32
PAPER_WORD_BITS = 256
PAPER_SECTOR_SIZE = 128 * 1024
PAPER_WORDS_PER_SECTOR = PAPER_SECTOR_SIZE // PAPER_WORD_BYTES

MT25Q_SIZE_BYTES = 32 * 1024 * 1024
MT25Q_SECTOR_SIZE = 0x10000
MT25Q_SUB32_SIZE = 0x8000
MT25Q_SUB4_SIZE = 0x1000
MT25Q_PAGE_SIZE = 0x100


@dataclass(frozen=True)
class SectorCoord:
    bank: int
    row: int
    col: int


def paper_word_index(row: int, col: int) -> int:
    return row * 256 + col


def sector_address_range(sector_id: int) -> tuple[int, int]:
    start = sector_id * MT25Q_SECTOR_SIZE
    end = start + MT25Q_SECTOR_SIZE - 1
    return start, end


def sub4_address_range(sub4_id: int) -> tuple[int, int]:
    start = sub4_id * MT25Q_SUB4_SIZE
    return start, start + MT25Q_SUB4_SIZE - 1


def sub32_address_range(sub32_id: int) -> tuple[int, int]:
    start = sub32_id * MT25Q_SUB32_SIZE
    return start, start + MT25Q_SUB32_SIZE - 1


def page_address_range(page_id: int) -> tuple[int, int]:
    start = page_id * MT25Q_PAGE_SIZE
    return start, start + MT25Q_PAGE_SIZE - 1


def mt25q_sector_to_grid(sector_id: int) -> SectorCoord:
    bank = sector_id // 256
    local = sector_id % 256
    col = local // 16
    row = local % 16
    return SectorCoord(bank=bank, row=row, col=col)


def grid_to_mt25q_sector(bank: int, row: int, col: int) -> int:
    return bank * 256 + col * 16 + row
