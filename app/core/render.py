"""Rendering helpers for sector thumbnails and detailed views."""

from __future__ import annotations

import hashlib
import numpy as np

from .ecc_overlay import ecc_matrix_for_sector

GREEN = np.array([50, 170, 80], dtype=np.uint8)
YELLOW = np.array([220, 210, 80], dtype=np.uint8)
DARK = np.array([20, 60, 30], dtype=np.uint8)


def _mix(c1, c2, t):
    return (c1 * (1 - t) + c2 * t).astype(np.uint8)


def sector_state_summary(sector_bytes: bytes) -> tuple[bool, float]:
    arr = np.frombuffer(sector_bytes, dtype=np.uint8)
    changed = np.count_nonzero(arr != 0xFF)
    ratio = float(changed) / float(arr.size)
    return changed == 0, ratio


def sector_thumbnail(sector_bytes: bytes, width: int = 128, height: int = 32, bitorder: str = "msb") -> np.ndarray:
    arr = np.frombuffer(sector_bytes, dtype=np.uint8).reshape(256, 256)
    bits = np.unpackbits(arr, axis=1, bitorder="big" if bitorder == "msb" else "little")
    band = bits.reshape(256, 256, 8).mean(axis=2)
    col_energy = band.mean(axis=1)
    row_energy = band.mean(axis=0)

    x = np.linspace(0, 255, width).astype(int)
    y = np.linspace(0, row_energy.size - 1, height).astype(int)

    base = col_energy[x][None, :]
    bands = row_energy[y][:, None]
    t = np.clip(0.2 + 0.8 * (0.6 * base + 0.4 * bands), 0, 1)
    img = _mix(GREEN, YELLOW, t[..., None])

    stripe = ((np.arange(width)[None, :] // max(1, width // 64)) % 2) * 0.08
    img = np.clip(img.astype(np.float32) * (0.92 + stripe[..., None]), 0, 255).astype(np.uint8)
    return img


def sector_detailed_image(sector_bytes: bytes, height: int = 180, with_ecc: bool = True, bitorder: str = "msb") -> np.ndarray:
    core = sector_thumbnail(sector_bytes, width=256, height=height, bitorder=bitorder)
    if not with_ecc:
        return core
    ecc = ecc_matrix_for_sector(sector_bytes)
    ecc_h = np.repeat(ecc, repeats=max(1, height // 10), axis=0)[:height, :]
    ecc_rgb = np.where(ecc_h[..., None] == 1, YELLOW, DARK)
    return np.concatenate([ecc_rgb, core], axis=1)


def thumbnail_hash(img: np.ndarray) -> str:
    return hashlib.sha256(img.tobytes()).hexdigest()
