from __future__ import annotations

from dataclasses import dataclass
import hashlib
import numpy as np

from .patterns import PatternSegment, generate_pattern


SECTOR_SIZE = 128 * 1024
SECTORS = 16
WORD_BITS_DEFAULT = 256
WORDS_PER_SECTOR = SECTOR_SIZE // (WORD_BITS_DEFAULT // 8)
BAND_COUNT = 256


@dataclass
class PaperPreset:
    sectors: list[bytes]


def build_paper_preset() -> PaperPreset:
    out: list[bytes] = []
    def text_full(s: str) -> bytes:
        return generate_pattern(SECTOR_SIZE, [PatternSegment(SECTOR_SIZE, "text", s)])

    s0 = text_full("D")
    s1 = text_full("Da")
    s2 = text_full("Data")
    s3 = text_full("Data Rec")
    s4 = text_full("Data Recovery vi")
    s5 = text_full("Data Recovery via Advanced Failu")
    s6 = generate_pattern(SECTOR_SIZE, [
        PatternSegment(64 * 1024, "text", "Data Recovery via Advanced Failure Analysis Techniques"),
        PatternSegment(64 * 1024, "fill", 0xFF),
    ])
    s7 = generate_pattern(SECTOR_SIZE, [PatternSegment(SECTOR_SIZE, "hex", "CC AA")])
    s8 = s5
    s9 = generate_pattern(SECTOR_SIZE, [PatternSegment(SECTOR_SIZE, "fill", 0x00)])
    s10 = s7
    s11 = s6
    s12 = s0
    s13 = text_full("d")
    s14 = generate_pattern(SECTOR_SIZE, [PatternSegment(SECTOR_SIZE, "fill", 0x55)])
    s15 = generate_pattern(SECTOR_SIZE, [PatternSegment(SECTOR_SIZE, "fill", 0xAA)])
    out.extend([s0,s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15])
    return PaperPreset(out)


def sector_band_bitmap(sector_data: bytes, band_index: int, word_bits: int = WORD_BITS_DEFAULT) -> np.ndarray:
    word_bytes = word_bits // 8
    words = np.frombuffer(sector_data, dtype=np.uint8).reshape(-1, word_bytes)
    bits = np.unpackbits(words, axis=1, bitorder="big")
    band_col = bits[:, band_index]
    # 4096 bits => 16x256 tile
    return band_col.reshape(16, 256)


def bitmap_hash(bitmap: np.ndarray) -> str:
    return hashlib.sha256(bitmap.astype(np.uint8).tobytes()).hexdigest()
