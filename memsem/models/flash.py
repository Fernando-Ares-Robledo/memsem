from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Region:
    start: int
    size: int


class FlashBuffer:
    def __init__(self, capacity_bytes: int):
        self.capacity_bytes = capacity_bytes
        self.data = bytearray(b"\xFF" * capacity_bytes)

    def _slice(self, region: Region) -> slice:
        start = max(0, region.start)
        end = min(self.capacity_bytes, region.start + region.size)
        return slice(start, end)

    def erase(self, region: Region) -> None:
        s = self._slice(region)
        self.data[s] = b"\xFF" * (s.stop - s.start)

    def program(self, region: Region, payload: bytes, enforce_nor_rule: bool = True) -> None:
        s = self._slice(region)
        old = self.data[s]
        incoming = payload[: len(old)]
        if len(incoming) < len(old):
            incoming += b"\xFF" * (len(old) - len(incoming))
        if enforce_nor_rule:
            self.data[s] = bytes([a & b for a, b in zip(old, incoming)])
        else:
            self.data[s] = incoming

    def read(self, region: Region) -> bytes:
        return bytes(self.data[self._slice(region)])

    def summary(self, region: Region) -> dict:
        block = self.read(region)
        size = len(block) or 1
        changed = sum(1 for b in block if b != 0xFF)
        return {
            "erased": changed == 0,
            "programmed": changed > 0,
            "ratio_changed": changed / size,
            "entropy": self._entropy_sample(block),
        }

    @staticmethod
    def _entropy_sample(block: bytes, sample_size: int = 4096) -> float:
        if not block:
            return 0.0
        stride = max(1, len(block) // sample_size)
        sample = block[::stride]
        hist = [0] * 256
        for b in sample:
            hist[b] += 1
        total = len(sample)
        entropy = 0.0
        for c in hist:
            if c:
                p = c / total
                entropy -= p * math.log2(p)
        return entropy / 8.0
