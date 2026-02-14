from __future__ import annotations

from core.constants import (
    PAGE_SIZE,
    PAGES_TOTAL,
    SECTOR_SIZE_64K,
    SECTORS_TOTAL,
    SUBSECTOR_SIZE_32K,
    SUBSECTOR_SIZE_4K,
    SUBSECTORS_32K_TOTAL,
    SUBSECTORS_4K_TOTAL,
)


def _range_for(index: int, unit_size: int, total: int) -> tuple[int, int]:
    if not 0 <= index < total:
        raise ValueError(f"index out of range: {index}")
    start = index * unit_size
    return start, start + unit_size - 1


def sector_range(sector_id: int) -> tuple[int, int]:
    return _range_for(sector_id, SECTOR_SIZE_64K, SECTORS_TOTAL)


def sub32_range(sub32_id: int) -> tuple[int, int]:
    return _range_for(sub32_id, SUBSECTOR_SIZE_32K, SUBSECTORS_32K_TOTAL)


def sub4_range(sub4_id: int) -> tuple[int, int]:
    return _range_for(sub4_id, SUBSECTOR_SIZE_4K, SUBSECTORS_4K_TOTAL)


def page_range(page_id: int) -> tuple[int, int]:
    return _range_for(page_id, PAGE_SIZE, PAGES_TOTAL)
