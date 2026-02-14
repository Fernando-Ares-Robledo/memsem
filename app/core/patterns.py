from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np


@dataclass
class Segment:
    size_kb: int
    type: str  # text | hex | fill
    value: str | int


def _parse_hex_string(value: str) -> bytes:
    cleaned = value.replace(",", " ").strip()
    parts = [p for p in cleaned.split() if p]
    out = []
    for part in parts:
        token = part.lower()
        if token.startswith("0x"):
            token = token[2:]
        out.append(int(token, 16))
    return bytes(out)


def _segment_to_chunk(segment: Segment) -> np.ndarray:
    if segment.type == "text":
        pattern = str(segment.value).encode("utf-8")
    elif segment.type == "hex":
        pattern = _parse_hex_string(str(segment.value))
    elif segment.type == "fill":
        b = int(segment.value)
        if b < 0 or b > 255:
            raise ValueError("fill value must be 0..255")
        pattern = bytes([b])
    else:
        raise ValueError(f"unknown segment type: {segment.type}")

    target_size = segment.size_kb * 1024
    if target_size <= 0:
        return np.zeros((0,), dtype=np.uint8)
    if not pattern:
        return np.full(target_size, 0xFF, dtype=np.uint8)

    rep = (target_size + len(pattern) - 1) // len(pattern)
    raw = (pattern * rep)[:target_size]
    return np.frombuffer(raw, dtype=np.uint8).copy()


def build_region_bytes(target_size: int, segments: Sequence[Segment]) -> np.ndarray:
    parts: List[np.ndarray] = []
    for seg in segments[:2]:
        parts.append(_segment_to_chunk(seg))
    merged = np.concatenate(parts) if parts else np.zeros((0,), dtype=np.uint8)

    if len(merged) < target_size:
        pad = np.full(target_size - len(merged), 0xFF, dtype=np.uint8)
        merged = np.concatenate([merged, pad])
    elif len(merged) > target_size:
        merged = merged[:target_size]
    return merged


def default_paper_preset() -> dict[int, list[Segment]]:
    long_text = "Data Recovery via Advanced Failure Analysis Techniques"
    return {
        0: [Segment(128, "text", "D")],
        1: [Segment(128, "text", "Da")],
        2: [Segment(128, "text", "Data")],
        3: [Segment(128, "text", "Data Rec")],
        4: [Segment(128, "text", "Data Recovery vi")],
        5: [Segment(128, "text", "Data Recovery via Advanced Failu")],
        6: [Segment(64, "text", long_text), Segment(64, "fill", 0xFF)],
        7: [Segment(128, "hex", "CC AA")],
        8: [Segment(128, "text", "Data Recovery via Advanced Failu")],
        9: [Segment(128, "fill", 0x00)],
        10: [Segment(128, "hex", "CC AA")],
        11: [Segment(64, "text", long_text), Segment(64, "fill", 0xFF)],
        12: [Segment(128, "text", "D")],
        13: [Segment(128, "text", "d")],
        14: [Segment(128, "fill", 0x55)],
        15: [Segment(128, "fill", 0xAA)],
    }
