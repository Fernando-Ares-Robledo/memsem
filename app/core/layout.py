"""Folded 64-sector layout, inverse mapping, and scene placement helpers."""

from __future__ import annotations

from dataclasses import dataclass

ARRAY_SECTORS = 256
BLOCK_SECTORS = 64
BLOCKS_PER_ARRAY = 4
BLOCK_ROWS = 17
BLOCK_COLS = 4
GAP_ROW = 8
TOTAL_SECTORS = 512


@dataclass(frozen=True)
class Cell:
    row: int
    col: int


@dataclass(frozen=True)
class SceneLayout:
    tile_w: int = 44
    tile_h: int = 30
    tile_gap: int = 2
    block_gap: int = 12
    array_gap: int = 20
    central_strip_h: int = 70
    margin: int = 10

    @property
    def block_w(self) -> int:
        return BLOCK_COLS * self.tile_w + (BLOCK_COLS - 1) * self.tile_gap

    @property
    def block_h(self) -> int:
        return BLOCK_ROWS * self.tile_h + (BLOCK_ROWS - 1) * self.tile_gap

    @property
    def array_w(self) -> int:
        return BLOCKS_PER_ARRAY * self.block_w + (BLOCKS_PER_ARRAY - 1) * self.block_gap


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


def inverse_folded64_cell(row: int, col: int) -> int:
    if row == GAP_ROW:
        raise ValueError("gap row has no sector")
    if not (0 <= row < BLOCK_ROWS and 0 <= col < BLOCK_COLS):
        raise ValueError("row/col out of range")
    group = 3 - col
    if row < 8:
        pos = row
    else:
        pos = 15 - (row - 9)
    return group * 16 + pos


def sector_to_array_block_local(sector_id: int) -> tuple[int, int, int]:
    if not 0 <= sector_id < TOTAL_SECTORS:
        raise ValueError("sector_id out of range")
    array_idx = 0 if sector_id < ARRAY_SECTORS else 1
    in_array = sector_id if array_idx == 0 else sector_id - ARRAY_SECTORS
    block_idx = in_array // BLOCK_SECTORS
    local_id = in_array % BLOCK_SECTORS
    return array_idx, block_idx, local_id


def sector_grid_position(sector_id: int) -> tuple[int, int, int]:
    array_idx, block_idx, local_id = sector_to_array_block_local(sector_id)
    cell = folded64_cell(local_id)
    global_col = block_idx * 4 + cell.col
    return array_idx, cell.row, global_col


def sector_scene_xy(sector_id: int, cfg: SceneLayout) -> tuple[int, int]:
    array_idx, block_idx, local_id = sector_to_array_block_local(sector_id)
    cell = folded64_cell(local_id)
    x = cfg.margin + block_idx * (cfg.block_w + cfg.block_gap) + cell.col * (cfg.tile_w + cfg.tile_gap)
    array0_origin_y = cfg.margin
    central_strip_y = array0_origin_y + cfg.block_h + cfg.array_gap
    array1_origin_y = central_strip_y + cfg.central_strip_h + cfg.array_gap
    y_base = array0_origin_y if array_idx == 0 else array1_origin_y
    y = y_base + cell.row * (cfg.tile_h + cfg.tile_gap)
    return x, y


def row_sector_ids(array_idx: int, row: int) -> list[int]:
    if array_idx not in (0, 1):
        raise ValueError("array_idx must be 0 or 1")
    if row == GAP_ROW or not (0 <= row < BLOCK_ROWS):
        raise ValueError("row must be 0..16 excluding 8")
    base = 0 if array_idx == 0 else ARRAY_SECTORS
    ids = []
    for b in range(BLOCKS_PER_ARRAY):
        for c in range(BLOCK_COLS):
            local_id = inverse_folded64_cell(row, c)
            ids.append(base + b * BLOCK_SECTORS + local_id)
    return ids


def row_strip_order(array_idx: int, row: int) -> tuple[list[int], list[int]]:
    ids = row_sector_ids(array_idx, row)
    left = ids[:8]
    right = list(reversed(ids[8:]))
    return left, right
