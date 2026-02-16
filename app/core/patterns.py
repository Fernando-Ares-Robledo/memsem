"""Pattern building logic used for program operations."""

from __future__ import annotations

from typing import Iterable


def _parse_hex_stream(text: str) -> bytes:
    clean = text.replace(",", " ").replace("0x", " ").replace("0X", " ")
    tokens = [tok for tok in clean.split() if tok]
    if not tokens:
        return b""
    vals = bytes(int(tok, 16) for tok in tokens)
    return vals


def _repeat_to_size(chunk: bytes, size: int) -> bytes:
    if size <= 0:
        return b""
    if not chunk:
        return bytes([0xFF]) * size
    times = (size + len(chunk) - 1) // len(chunk)
    return (chunk * times)[:size]


def segment_to_bytes(seg_type: str, value, size_bytes: int) -> bytes:
    if seg_type == "text":
        payload = str(value).encode("utf-8")
    elif seg_type == "hex":
        payload = _parse_hex_stream(str(value))
    elif seg_type == "fill":
        text = str(value).strip()
        # Accept both decimal (170) and prefixed bases (0xAA, 0b1010, 0o12).
        v = int(text, 0) if text else 0
        if not 0 <= v <= 255:
            raise ValueError("fill value must be 0..255")
        payload = bytes([v])
    else:
        raise ValueError(f"Unknown segment type: {seg_type}")
    return _repeat_to_size(payload, size_bytes)


def build_pattern_bytes(pattern_segments: Iterable[dict], target_size: int) -> bytes:
    out = bytearray()
    for segment in pattern_segments:
        size = int(segment["size_bytes"])
        if size <= 0:
            continue
        out.extend(segment_to_bytes(segment["type"], segment.get("value", ""), size))
        if len(out) >= target_size:
            return bytes(out[:target_size])
    if len(out) < target_size:
        out.extend([0xFF] * (target_size - len(out)))
    return bytes(out[:target_size])
