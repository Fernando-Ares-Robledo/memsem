"""Memory model and programming/erase operations."""

from __future__ import annotations

from dataclasses import dataclass

from .addressing import CAPACITY_BYTES, MAX_ADDRESS
from .patterns import build_pattern_bytes


@dataclass
class MemoryModel:
    enforce_nor: bool = True

    def __post_init__(self):
        self.mem = bytearray([0xFF] * CAPACITY_BYTES)

    def read(self, start: int, size: int) -> bytes:
        self._validate_region(start, size)
        return bytes(self.mem[start : start + size])

    def erase(self, region_start: int, region_size: int) -> None:
        self._validate_region(region_start, region_size)
        self.mem[region_start : region_start + region_size] = b"\xFF" * region_size

    def program(self, region_start: int, region_size: int, pattern_segments: list[dict], enforce_nor: bool | None = None):
        self._validate_region(region_start, region_size)
        data = build_pattern_bytes(pattern_segments, region_size)
        nor = self.enforce_nor if enforce_nor is None else enforce_nor
        if nor:
            for i in range(region_size):
                self.mem[region_start + i] &= data[i]
        else:
            self.mem[region_start : region_start + region_size] = data

    def _validate_region(self, start: int, size: int):
        if size < 0:
            raise ValueError("negative size")
        end = start + size - 1 if size else start
        if start < 0 or end > MAX_ADDRESS:
            raise ValueError("region out of range")
