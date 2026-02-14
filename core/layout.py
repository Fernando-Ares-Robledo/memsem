from __future__ import annotations

from dataclasses import dataclass

from core.constants import LayoutConfig


@dataclass(frozen=True)
class CellPlacement:
    sector_id: int
    bank: int
    block_index: int
    local_id: int
    row: int
    col: int
    x: int
    y: int


def folded64_local_to_cell(local_id: int) -> tuple[int, int]:
    if not 0 <= local_id < 64:
        raise ValueError("local_id must be in [0,63]")
    group = local_id // 16
    pos = local_id % 16
    col = 3 - group
    if pos < 8:
        row = pos
    else:
        row = (15 - pos) + 9
    return row, col


def sector_to_layout_cell(sector_id: int, cfg: LayoutConfig) -> CellPlacement:
    bank = 0 if sector_id < 256 else 1
    bank_local = sector_id - bank * 256
    block_index = bank_local // 64
    local_id = bank_local % 64
    row, col = folded64_local_to_cell(local_id)
    x = block_index * cfg.block_width_in_cells + col
    y = bank * (cfg.block_height_in_cells + 1) + row
    return CellPlacement(sector_id, bank, block_index, local_id, row, col, x, y)


def iter_visible_sectors(cfg: LayoutConfig) -> list[CellPlacement]:
    placements: list[CellPlacement] = []
    for sid in range(512):
        p = sector_to_layout_cell(sid, cfg)
        if p.bank == 0 and p.block_index in cfg.hide_blocks_bank0:
            continue
        if p.bank == 1 and p.block_index in cfg.hide_blocks_bank1:
            continue
        if cfg.show_sectors_per_bank is not None:
            bank_local = sid if sid < 256 else sid - 256
            if bank_local >= cfg.show_sectors_per_bank:
                continue
        placements.append(p)
    return placements
