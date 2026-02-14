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


def sector_thumbnail(sector_bytes: bytes, width: int = 128, height: int = 32, bitorder: str = "msb", orientation: str = "horizontal") -> np.ndarray:
    arr = np.frombuffer(sector_bytes, dtype=np.uint8).reshape(256, 256)
    bits = np.unpackbits(arr, axis=1, bitorder="big" if bitorder == "msb" else "little")

    if orientation not in ("horizontal", "vertical"):
        raise ValueError("orientation must be horizontal|vertical")

    col_signal = bits.mean(axis=1)  # page-driven
    row_signal = bits.mean(axis=0)  # bitplane-driven

    if orientation == "horizontal":
        col_idx = np.linspace(0, 255, width).astype(int)
        row_idx = np.linspace(0, row_signal.size - 1, height).astype(int)
        col = col_signal[col_idx][None, :]
        row = row_signal[row_idx][:, None]
    else:
        # Paper-like orientation: page progression on vertical axis.
        col_idx = np.linspace(0, row_signal.size - 1, width).astype(int)
        row_idx = np.linspace(0, 255, height).astype(int)
        col = row_signal[col_idx][None, :]
        row = col_signal[row_idx][:, None]

    # 0->GREEN, 1->YELLOW while preserving clear horizontal banding.
    t = np.clip(0.08 + 0.92 * (0.35 * col + 0.65 * row), 0, 1)
    img = _mix(GREEN, YELLOW, t[..., None])

    # Deterministic engraving-like stripes and dataset separators.
    stripe_h = ((np.arange(height)[:, None] // max(1, height // 12)) % 2) * 0.20
    stripe_v = ((np.arange(width)[None, :] // max(1, width // 64)) % 2) * 0.10
    img = np.clip(img.astype(np.float32) * (0.78 + stripe_h[..., None] + stripe_v[..., None]), 0, 255).astype(np.uint8)
    return img


def sector_detailed_image(sector_bytes: bytes, height: int = 180, with_ecc: bool = True, bitorder: str = "msb", orientation: str = "horizontal") -> np.ndarray:
    width = 256 if orientation == "horizontal" else 96
    core = sector_thumbnail(sector_bytes, width=width, height=height, bitorder=bitorder, orientation=orientation)
    if not with_ecc:
        return core
    ecc = ecc_matrix_for_sector(sector_bytes)
    ecc_h = np.repeat(ecc, repeats=max(1, height // 10), axis=0)[:height, :]
    ecc_rgb = np.where(ecc_h[..., None] == 1, YELLOW, DARK)
    return np.concatenate([ecc_rgb, core], axis=1)


def thumbnail_hash(img: np.ndarray) -> str:
    return hashlib.sha256(img.tobytes()).hexdigest()
