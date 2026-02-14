"""Rendering helpers for sector thumbnails and detailed views."""

from __future__ import annotations

import hashlib
import numpy as np

from .ecc_overlay import ecc_matrix_for_sector

# Visual convention tuned to resemble lab/paper-like captures:
# erased(1) -> green background, programmed(0) -> yellow bands.
GREEN = np.array([35, 170, 70], dtype=np.uint8)
YELLOW = np.array([230, 220, 70], dtype=np.uint8)
DARK = np.array([20, 60, 30], dtype=np.uint8)


def _mix(c1, c2, t):
    return (c1 * (1 - t) + c2 * t).astype(np.uint8)


def _smooth1d(x: np.ndarray, repeats: int = 2) -> np.ndarray:
    k = np.array([1, 2, 3, 2, 1], dtype=np.float32)
    k = k / k.sum()
    y = x.astype(np.float32)
    for _ in range(repeats):
        y = np.convolve(y, k, mode="same")
    return y


def sector_state_summary(sector_bytes: bytes) -> tuple[bool, float]:
    arr = np.frombuffer(sector_bytes, dtype=np.uint8)
    changed = np.count_nonzero(arr != 0xFF)
    ratio = float(changed) / float(arr.size)
    return changed == 0, ratio


def sector_thumbnail(
    sector_bytes: bytes,
    width: int = 128,
    height: int = 32,
    bitorder: str = "msb",
    orientation: str = "horizontal",
) -> np.ndarray:
    arr = np.frombuffer(sector_bytes, dtype=np.uint8).reshape(256, 256)
    bits = np.unpackbits(arr, axis=1, bitorder="big" if bitorder == "msb" else "little")

    if orientation not in ("horizontal", "vertical"):
        raise ValueError("orientation must be horizontal|vertical")

    # zero-ratio (programmed intensity) signals.
    page_zero = 1.0 - bits.mean(axis=1)  # 256 samples, one per page
    bitline_zero = 1.0 - bits.mean(axis=0)  # 2048 samples across bitlines

    page_zero = _smooth1d(page_zero, repeats=2)
    bitline_zero = _smooth1d(bitline_zero, repeats=2)

    if orientation == "horizontal":
        xi = np.linspace(0, 255, width).astype(int)
        yi = np.linspace(0, bitline_zero.size - 1, height).astype(int)
        col = page_zero[xi][None, :]
        row = bitline_zero[yi][:, None]
        t = np.clip(0.20 + 0.80 * (0.30 * col + 0.70 * row), 0, 1)
    else:
        # Paper-like: sector is tall, pages progress vertically.
        xi = np.linspace(0, bitline_zero.size - 1, width).astype(int)
        yi = np.linspace(0, 255, height).astype(int)
        col = bitline_zero[xi][None, :]
        row = page_zero[yi][:, None]
        t = np.clip(0.18 + 0.82 * (0.55 * row + 0.45 * col), 0, 1)

    img = _mix(GREEN, YELLOW, t[..., None])

    # Mild separators (avoid checkerboard look).
    if orientation == "horizontal":
        sep = ((np.arange(width)[None, :] // max(1, width // 64)) % 2) * 0.06
    else:
        sep = ((np.arange(height)[:, None] // max(1, height // 16)) % 2) * 0.08
    img = np.clip(img.astype(np.float32) * (0.94 + sep[..., None]), 0, 255).astype(np.uint8)
    return img


def sector_detailed_image(
    sector_bytes: bytes,
    height: int = 180,
    with_ecc: bool = True,
    bitorder: str = "msb",
    orientation: str = "horizontal",
) -> np.ndarray:
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
