from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PatternSegment:
    kind: str  # text | hex | fill
    value: str

    def to_bytes(self) -> bytes:
        if self.kind == "text":
            return self.value.encode("utf-8")
        if self.kind == "hex":
            cleaned = self.value.replace(",", " ").strip()
            if not cleaned:
                return b""
            return bytes(int(tok, 16) for tok in cleaned.split())
        if self.kind == "fill":
            v = int(self.value, 16) if self.value.lower().startswith("0x") else int(self.value)
            return bytes([v & 0xFF])
        raise ValueError(f"Unsupported segment kind: {self.kind}")


def build_pattern(region_size: int, segments: list[PatternSegment]) -> bytes:
    if not segments:
        return bytes([0xFF]) * region_size
    src = b"".join(seg.to_bytes() for seg in segments)
    if not src:
        return bytes([0xFF]) * region_size
    repeats = (region_size + len(src) - 1) // len(src)
    out = (src * repeats)[:region_size]
    if len(out) < region_size:
        out += bytes([0xFF]) * (region_size - len(out))
    return out
