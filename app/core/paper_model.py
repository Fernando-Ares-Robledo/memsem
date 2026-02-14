from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1

import numpy as np

from .mapping import PAPER_SECTOR_SIZE, PAPER_WORD_BITS, PAPER_WORD_BYTES, PAPER_WORDS_PER_SECTOR, paper_word_index
from .patterns import Segment, build_region_bytes, default_paper_preset
from .state_cache import LRUCache


@dataclass
class PaperSelection:
    sector_id: int
    band: int
    row: int
    col: int


class PaperModel:
    def __init__(self, bitorder: str = "big"):
        self.bitorder = bitorder
        self.segments = default_paper_preset()
        self._bytes_cache = LRUCache(64)
        self._bits_cache = LRUCache(64)

    def set_segment_config(self, sector_id: int, segments: list[Segment]) -> None:
        self.segments[sector_id] = segments
        self._bytes_cache.clear()
        self._bits_cache.clear()

    def sector_bytes(self, sector_id: int) -> np.ndarray:
        key = f"sector-bytes-{sector_id}"
        cached = self._bytes_cache.get(key)
        if cached is not None:
            return cached
        data = build_region_bytes(PAPER_SECTOR_SIZE, self.segments.get(sector_id, []))
        self._bytes_cache.put(key, data)
        return data

    def sector_words_bits(self, sector_id: int) -> np.ndarray:
        key = f"sector-bits-{sector_id}-{self.bitorder}"
        cached = self._bits_cache.get(key)
        if cached is not None:
            return cached

        raw = self.sector_bytes(sector_id)
        words = raw.reshape(PAPER_WORDS_PER_SECTOR, PAPER_WORD_BYTES)
        bits = np.unpackbits(words, axis=1, bitorder=self.bitorder)
        self._bits_cache.put(key, bits)
        return bits

    def band_tile(self, sector_id: int, band: int, c_start: int = 0, width: int = 256) -> np.ndarray:
        bits = self.sector_words_bits(sector_id)
        out = np.zeros((16, width), dtype=np.uint8)
        for r in range(16):
            for ci, c in enumerate(range(c_start, c_start + width)):
                wi = paper_word_index(r, c)
                out[r, ci] = bits[wi, band]
        return out

    def selected_word_bytes(self, sector_id: int, row: int, col: int) -> np.ndarray:
        data = self.sector_bytes(sector_id)
        wi = paper_word_index(row, col)
        start = wi * PAPER_WORD_BYTES
        end = start + PAPER_WORD_BYTES
        return data[start:end]

    def sector_signature(self, sector_id: int) -> str:
        return sha1(self.sector_bytes(sector_id).tobytes()).hexdigest()

    def bank_layout(self) -> tuple[list[int], list[int]]:
        return list(range(0, 8)), list(range(15, 7, -1))
