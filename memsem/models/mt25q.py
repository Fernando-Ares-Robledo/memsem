from __future__ import annotations

CAPACITY_BYTES = 32 * 1024 * 1024
SECTOR_SIZE = 0x10000
SUB32_SIZE = 0x8000
SUB4_SIZE = 0x1000
PAGE_SIZE = 0x100

SECTORS = CAPACITY_BYTES // SECTOR_SIZE
SUB32S = CAPACITY_BYTES // SUB32_SIZE
SUB4S = CAPACITY_BYTES // SUB4_SIZE
PAGES = CAPACITY_BYTES // PAGE_SIZE


def range_for_sector(sector_id: int) -> tuple[int, int]:
    start = sector_id * SECTOR_SIZE
    return start, start + SECTOR_SIZE - 1


def range_for_sub32(sub_id: int) -> tuple[int, int]:
    start = sub_id * SUB32_SIZE
    return start, start + SUB32_SIZE - 1


def range_for_sub4(sub_id: int) -> tuple[int, int]:
    start = sub_id * SUB4_SIZE
    return start, start + SUB4_SIZE - 1


def range_for_page(page_id: int) -> tuple[int, int]:
    start = page_id * PAGE_SIZE
    return start, start + PAGE_SIZE - 1


def sector_segment(sector_id: int) -> int:
    return 0 if sector_id <= 255 else 1


def reference_rows() -> dict[str, list[tuple[int, int, int]]]:
    return {
        "sector64": [(i, *range_for_sector(i)) for i in (0, 1, 255, 256, 511)],
        "sub32": [(i, *range_for_sub32(i)) for i in (0, 1, 1023)],
        "sub4": [(i, *range_for_sub4(i)) for i in (0, 1, 8191)],
    }
