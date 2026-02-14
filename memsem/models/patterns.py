from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class PatternSegment:
    size_bytes: int
    type: str  # text | hex | fill
    value: str | int


def _parse_hex_pattern(value: str) -> bytes:
    tokens = re.split(r"[\s,]+", value.strip())
    out = []
    for tok in tokens:
        if not tok:
            continue
        tok = tok.lower()
        if tok.startswith("0x"):
            tok = tok[2:]
        if len(tok) == 1:
            tok = f"0{tok}"
        out.append(int(tok, 16) & 0xFF)
    if not out:
        raise ValueError("hex pattern has no bytes")
    return bytes(out)


def _segment_seed_bytes(segment: PatternSegment) -> bytes:
    if segment.type == "text":
        bs = str(segment.value).encode("utf-8")
    elif segment.type == "hex":
        bs = _parse_hex_pattern(str(segment.value))
    elif segment.type == "fill":
        bs = bytes([int(segment.value) & 0xFF])
    else:
        raise ValueError(f"unknown segment type: {segment.type}")
    if not bs:
        raise ValueError("segment expands to empty seed")
    return bs


def _repeat_to_length(seed: bytes, length: int) -> bytes:
    if length <= 0:
        return b""
    repeats = (length + len(seed) - 1) // len(seed)
    return (seed * repeats)[:length]


def generate_pattern(region_size: int, segments: Iterable[PatternSegment]) -> bytes:
    output = bytearray()
    for seg in segments:
        if len(output) >= region_size:
            break
        chunk_len = max(0, int(seg.size_bytes))
        seed = _segment_seed_bytes(seg)
        output.extend(_repeat_to_length(seed, chunk_len))

    if len(output) < region_size:
        output.extend(b"\xFF" * (region_size - len(output)))
    return bytes(output[:region_size])
