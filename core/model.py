from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from core.constants import (
    LayoutConfig,
    PAGE_SIZE,
    SECTOR_SIZE_64K,
    SUBSECTOR_SIZE_32K,
    SUBSECTOR_SIZE_4K,
    TOTAL_BYTES,
)


@dataclass
class Selection:
    start: int
    size: int
    level: str

    @property
    def end(self) -> int:
        return self.start + self.size - 1


class FlashModel:
    def __init__(self) -> None:
        self.data = np.full(TOTAL_BYTES, 0xFF, dtype=np.uint8)
        self.layout = LayoutConfig()

    def erase(self, start: int, size: int) -> None:
        self.data[start : start + size] = 0xFF

    def program(self, start: int, payload: bytes, enforce_nor_rule: bool = True) -> None:
        arr = np.frombuffer(payload, dtype=np.uint8)
        end = start + len(arr)
        if enforce_nor_rule:
            self.data[start:end] = self.data[start:end] & arr
        else:
            self.data[start:end] = arr

    def summary_ratio_non_ff(self, start: int, size: int) -> float:
        region = self.data[start : start + size]
        return float(np.count_nonzero(region != 0xFF)) / float(size)

    def sector_ratio(self, sector_id: int) -> float:
        return self.summary_ratio_non_ff(sector_id * SECTOR_SIZE_64K, SECTOR_SIZE_64K)

    def get_bytes(self, start: int, size: int) -> bytes:
        return self.data[start : start + size].tobytes()

    def bit_plane(
        self,
        start: int,
        size: int,
        word_bits: int = 256,
        plane: int = 0,
        msb_first: bool = True,
    ) -> np.ndarray:
        raw = self.data[start : start + size]
        bits = np.unpackbits(raw, bitorder="big" if msb_first else "little")
        words = len(bits) // word_bits
        trimmed = bits[: words * word_bits]
        if words == 0:
            return np.zeros((0, 0), dtype=np.uint8)
        mat = trimmed.reshape((words, word_bits))
        return mat[:, plane]

    def save_project(self, path: Path, bin_path: Path, ui_settings: dict) -> None:
        bin_path.write_bytes(self.data.tobytes())
        payload = {
            "layout": asdict(self.layout),
            "memory_bin": str(bin_path.name),
            "ui_settings": ui_settings,
        }
        path.write_text(json.dumps(payload, indent=2))

    def load_project(self, path: Path) -> dict:
        payload = json.loads(path.read_text())
        self.layout = LayoutConfig(**payload["layout"])
        bin_file = path.parent / payload["memory_bin"]
        self.data = np.frombuffer(bin_file.read_bytes(), dtype=np.uint8).copy()
        return payload.get("ui_settings", {})


REGION_SIZES = {
    "sector64": SECTOR_SIZE_64K,
    "sub32": SUBSECTOR_SIZE_32K,
    "sub4": SUBSECTOR_SIZE_4K,
    "page": PAGE_SIZE,
}
