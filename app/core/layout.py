"""Folded 64-sector layout and two-array placement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cell:
    row: int
    col: int


def folded64_cell(local_id: int) -> Cell:
    if not 0 <= local_id < 64:
        raise ValueError("local_id must be 0..63")
    group = local_id // 16
    pos = local_id % 16
    col = 3 - group
    if pos < 8:
        row = pos
    else:
        row = (15 - pos) + 9
    return Cell(row=row, col=col)


def sector_to_array_block_local(sector_id: int) -> tuple[int, int, int]:
    if not 0 <= sector_id < 512:
        raise ValueError("sector_id out of range")
    array_idx = 0 if sector_id < 256 else 1
    in_array = sector_id if array_idx == 0 else sector_id - 256
    block_idx = in_array // 64
    local_id = in_array % 64
    return array_idx, block_idx, local_id


def sector_grid_position(sector_id: int, blocks_per_array: int = 4) -> tuple[int, int, int]:
    array_idx, block_idx, local_id = sector_to_array_block_local(sector_id)
    cell = folded64_cell(local_id)
    global_col = block_idx * 4 + cell.col
    return array_idx, cell.row, global_col
