from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .mapping import (
    MT25Q_PAGE_SIZE,
    MT25Q_SECTOR_SIZE,
    MT25Q_SIZE_BYTES,
    MT25Q_SUB4_SIZE,
    MT25Q_SUB32_SIZE,
    mt25q_sector_to_grid,
    sector_address_range,
)
from .patterns import Segment, build_region_bytes


@dataclass
class RegionSelection:
    start: int
    size: int


class MT25QModel:
    def __init__(self):
        self.memory = np.full((MT25Q_SIZE_BYTES,), 0xFF, dtype=np.uint8)
        self.nor_enforced = False

    def set_nor_enforced(self, enabled: bool) -> None:
        self.nor_enforced = enabled

    def erase(self, start: int, size: int) -> None:
        self.memory[start:start + size] = 0xFF

    def program(self, start: int, size: int, segments: list[Segment]) -> None:
        data = build_region_bytes(size, segments)
        if self.nor_enforced:
            self.memory[start:start + size] = self.memory[start:start + size] & data
        else:
            self.memory[start:start + size] = data

    def sector_state(self, sector_id: int) -> tuple[bool, float]:
        start, end = sector_address_range(sector_id)
        view = self.memory[start:end + 1]
        programmed = bool(np.any(view != 0xFF))
        density = float(np.mean(view != 0xFF))
        return programmed, density

    def jump_to_address(self, addr: int) -> dict:
        sector = addr // MT25Q_SECTOR_SIZE
        sector_start, _ = sector_address_range(sector)
        return {
            "address": addr,
            "sector_id": sector,
            "bank_coord": mt25q_sector_to_grid(sector),
            "sub32_id": addr // MT25Q_SUB32_SIZE,
            "sub4_id": addr // MT25Q_SUB4_SIZE,
            "page_id": addr // MT25Q_PAGE_SIZE,
            "offset_in_sector": addr - sector_start,
        }
