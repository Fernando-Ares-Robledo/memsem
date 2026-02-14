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
PERIPHERY_A = np.array([190, 150, 190], dtype=np.uint8)
PERIPHERY_B = np.array([150, 170, 210], dtype=np.uint8)


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


def _vertical_like_real(page_zero: np.ndarray, bitline_zero: np.ndarray, width: int, height: int) -> np.ndarray:
    yi = np.linspace(0, 255, height).astype(int)
    xi = np.linspace(0, bitline_zero.size - 1, width).astype(int)

    row = _smooth1d(page_zero[yi], repeats=2)[:, None]
    col = _smooth1d(bitline_zero[xi], repeats=2)[None, :]

    x = np.linspace(0, 1, width)[None, :]
    # Main active region tends to the right half in paper-like captures.
    right_window = np.clip((x - 0.55) / 0.35, 0, 1)
    # faint structure on the left
    left_window = np.clip((0.35 - x) / 0.35, 0, 1)

    t = 0.06 + 0.94 * (
        0.78 * row * (0.35 + 0.65 * right_window)
        + 0.12 * col * right_window
        + 0.10 * row * left_window * 0.35
    )
    t = np.clip(t, 0, 1)
    img = _mix(GREEN, YELLOW, t[..., None])

    # horizontal band emphasis
    stripe_h = ((np.arange(height)[:, None] // max(1, height // 18)) % 2) * 0.09
    img = np.clip(img.astype(np.float32) * (0.93 + stripe_h[..., None]), 0, 255).astype(np.uint8)
    return img


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

    if orientation == "vertical":
        return _vertical_like_real(page_zero, bitline_zero, width, height)

    page_zero = _smooth1d(page_zero, repeats=2)
    bitline_zero = _smooth1d(bitline_zero, repeats=2)
    xi = np.linspace(0, 255, width).astype(int)
    yi = np.linspace(0, bitline_zero.size - 1, height).astype(int)
    col = page_zero[xi][None, :]
    row = bitline_zero[yi][:, None]
    t = np.clip(0.20 + 0.80 * (0.30 * col + 0.70 * row), 0, 1)

    img = _mix(GREEN, YELLOW, t[..., None])
    sep = ((np.arange(width)[None, :] // max(1, width // 64)) % 2) * 0.06
    img = np.clip(img.astype(np.float32) * (0.94 + sep[..., None]), 0, 255).astype(np.uint8)
    return img


def _periphery_strip(height: int, width: int) -> np.ndarray:
    y = np.arange(height)[:, None]
    pattern = (y // max(1, height // 64)) % 2
    strip = np.where(pattern[..., None] == 1, PERIPHERY_A, PERIPHERY_B)
    return np.repeat(strip, width, axis=1)


def sector_detailed_image(
    sector_bytes: bytes,
    height: int = 180,
    with_ecc: bool = True,
    bitorder: str = "msb",
    orientation: str = "horizontal",
) -> np.ndarray:
    width = 256 if orientation == "horizontal" else 96
    core = sector_thumbnail(sector_bytes, width=width, height=height, bitorder=bitorder, orientation=orientation)

    if orientation == "vertical":
        left = _periphery_strip(height, 6)
        right = _periphery_strip(height, 6)
        core = np.concatenate([left, core, right], axis=1)

    if not with_ecc:
        return core

    ecc = ecc_matrix_for_sector(sector_bytes)
    ecc_h = np.repeat(ecc, repeats=max(1, height // 10), axis=0)[:height, :]
    ecc_rgb = np.where(ecc_h[..., None] == 1, YELLOW, DARK)
    return np.concatenate([ecc_rgb, core], axis=1)


def thumbnail_hash(img: np.ndarray) -> str:
    return hashlib.sha256(img.tobytes()).hexdigest()
