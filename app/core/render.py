"""Rendering helpers for sector thumbnails and detailed views."""

from __future__ import annotations

import hashlib
import numpy as np

from .ecc_overlay import ecc_matrix_for_sector

GREEN = np.array([25, 150, 55], dtype=np.uint8)
YELLOW = np.array([235, 220, 40], dtype=np.uint8)
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

    # Sample the 256x2048 bit-plane into requested thumbnail size using nearest bins.
    x = np.linspace(0, 255, width).astype(int)
    y = np.linspace(0, bits.shape[1] - 1, height).astype(int)
    sampled = bits[x][:, y].T  # (height, width), values in {0,1}

    # Explicit 0/1 color map for visual debugging: 0->green, 1->yellow.
    img = np.where(sampled[..., None] == 1, YELLOW, GREEN).astype(np.uint8)

    # Add deterministic separators so datasets/bands remain easy to perceive.
    dataset_sep = ((np.arange(width)[None, :] // max(1, width // 64)) % 2) * 0.12
    banding = ((np.arange(height)[:, None] // max(1, height // 8)) % 2) * 0.08
    img = np.clip(img.astype(np.float32) * (0.86 + dataset_sep[..., None] + banding[..., None]), 0, 255).astype(np.uint8)
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
