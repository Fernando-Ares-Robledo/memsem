from __future__ import annotations

from dataclasses import dataclass

from .addressing import SECTOR_SIZE, sector_start
from .render import sector_thumbnail, thumbnail_hash


@dataclass(frozen=True)
class ValidationResult:
    pair: tuple[int, int]
    hash_a: str
    hash_b: str
    match: bool


def apply_paper_like_preset(model) -> None:
    patterns = {
        0: [{"type": "text", "size_bytes": SECTOR_SIZE, "value": "D"}],
        1: [{"type": "text", "size_bytes": SECTOR_SIZE, "value": "Da"}],
        2: [{"type": "text", "size_bytes": SECTOR_SIZE, "value": "Data"}],
        3: [{"type": "text", "size_bytes": SECTOR_SIZE, "value": "Data Rec"}],
        4: [{"type": "text", "size_bytes": SECTOR_SIZE, "value": "Data Recovery vi"}],
        5: [{"type": "text", "size_bytes": SECTOR_SIZE, "value": "Data Recovery via Advanced Failu"}],
        6: [
            {"type": "text", "size_bytes": 0x8000, "value": "Data Recovery via Advanced Failure Analysis Techniques"},
            {"type": "fill", "size_bytes": 0x8000, "value": 0xFF},
        ],
        7: [{"type": "hex", "size_bytes": SECTOR_SIZE, "value": "CC AA"}],
        8: [{"type": "text", "size_bytes": SECTOR_SIZE, "value": "Data Recovery via Advanced Failu"}],
        9: [{"type": "fill", "size_bytes": SECTOR_SIZE, "value": 0x00}],
        10: [{"type": "hex", "size_bytes": SECTOR_SIZE, "value": "CC AA"}],
        11: [
            {"type": "text", "size_bytes": 0x8000, "value": "Data Recovery via Advanced Failure Analysis Techniques"},
            {"type": "fill", "size_bytes": 0x8000, "value": 0xFF},
        ],
        12: [{"type": "text", "size_bytes": SECTOR_SIZE, "value": "D"}],
        13: [{"type": "text", "size_bytes": SECTOR_SIZE, "value": "d"}],
        14: [{"type": "fill", "size_bytes": SECTOR_SIZE, "value": 0x55}],
        15: [{"type": "fill", "size_bytes": SECTOR_SIZE, "value": 0xAA}],
    }
    for sid in range(16):
        start = sector_start(sid)
        model.erase(start, SECTOR_SIZE)
        model.program(start, SECTOR_SIZE, patterns[sid], enforce_nor=True)


def validate_paper_like_hashes(model, bitorder: str = "msb") -> tuple[dict[int, str], list[ValidationResult]]:
    hashes: dict[int, str] = {}
    for sid in range(16):
        start = sector_start(sid)
        thumb = sector_thumbnail(model.read(start, SECTOR_SIZE), width=48, height=32, bitorder=bitorder)
        hashes[sid] = thumbnail_hash(thumb)

    pairs = [(0, 12), (7, 10), (5, 8), (6, 11)]
    results = [
        ValidationResult(pair=p, hash_a=hashes[p[0]], hash_b=hashes[p[1]], match=hashes[p[0]] == hashes[p[1]])
        for p in pairs
    ]
    return hashes, results
