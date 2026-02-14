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

_POPCOUNT = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


def _mix(c1, c2, t):
    return (c1 * (1 - t) + c2 * t).astype(np.uint8)


def _smooth1d(x: np.ndarray, repeats: int = 2) -> np.ndarray:
    k = np.array([1, 2, 1], dtype=np.float32)
    k = k / k.sum()
    y = x.astype(np.float32)
    for _ in range(repeats):
        y = np.convolve(y, k, mode="same")
    return y


def _smooth2d_light(x: np.ndarray) -> np.ndarray:
    """Very light separable [1,2,1]/4 smoothing, 1 pass each axis."""
    k = np.array([1.0, 2.0, 1.0], dtype=np.float32) / 4.0
    # horizontal
    tmp = np.pad(x.astype(np.float32), ((0, 0), (1, 1)), mode="edge")
    h = tmp[:, :-2] * k[0] + tmp[:, 1:-1] * k[1] + tmp[:, 2:] * k[2]
    # vertical
    tmp2 = np.pad(h, ((1, 1), (0, 0)), mode="edge")
    v = tmp2[:-2, :] * k[0] + tmp2[1:-1, :] * k[1] + tmp2[2:, :] * k[2]
    return v


def sector_state_summary(sector_bytes: bytes) -> tuple[bool, float]:
    arr = np.frombuffer(sector_bytes, dtype=np.uint8)
    changed = np.count_nonzero(arr != 0xFF)
    ratio = float(changed) / float(arr.size)
    return changed == 0, ratio


def sector_band_image(
    sector_bytes: bytes,
    out_w: int,
    out_h: int,
    bitorder: str = "msb",
    word_bits: int = 256,
) -> np.ndarray:
    """
    Paper-like band rendering.
    Builds a (word_bits*16) x cols binary matrix from bit-planes, then downsamples to out_h x out_w.
    bit=1 (erased) -> GREEN, bit=0 -> YELLOW.
    """
    arr = np.frombuffer(sector_bytes, dtype=np.uint8)
    bits = np.unpackbits(arr, bitorder="big" if bitorder == "msb" else "little")

    total_bits = (bits.size // word_bits) * word_bits
    bits = bits[:total_bits]
    words = bits.reshape(-1, word_bits)  # (words_count, word_bits)
    words_count = words.shape[0]

    cols = (words_count + 15) // 16
    padded_words = np.ones((cols * 16, word_bits), dtype=np.uint8)  # pad with erased=1
    padded_words[:words_count, :] = words

    # Build big band matrix: (word_bits*16, cols)
    # plane b => 16 x cols tile
    band_h = word_bits * 16
    band_w = cols
    band = np.empty((band_h, band_w), dtype=np.uint8)

    # Fill band block by block: each plane occupies 16 rows
    for b in range(word_bits):
        plane = padded_words[:, b].reshape(cols, 16).T  # (16, cols)
        band[b * 16 : (b + 1) * 16, :] = plane

    # Downsample band -> out_h x out_w using pooling (fast because dimensions divide nicely often)
    # First vertical pooling
    if band_h % out_h == 0:
        vh = band_h // out_h
        band_ds = band.reshape(out_h, vh, band_w).mean(axis=1)
    else:
        yi = np.linspace(0, band_h - 1, out_h).astype(int)
        band_ds = band[yi, :].astype(np.float32)

    # Then horizontal pooling
    if band_w % out_w == 0:
        vw = band_w // out_w
        band_ds = band_ds.reshape(out_h, out_w, vw).mean(axis=2)
    else:
        xi = np.linspace(0, band_w - 1, out_w).astype(int)
        band_ds = band_ds[:, xi]

    # Very light 2D smoothing for LOD2/strip only.
    band_ds = _smooth2d_light(band_ds)

    # band_ds is mean bit value in [0,1]. We want t = zero_ratio = 1 - mean_bit
    t = (1.0 - band_ds).astype(np.float32)
    t = np.clip(t, 0.0, 1.0)

    img = _mix(GREEN, YELLOW, t[..., None])

    # subtle separators to look more “captured”
    sep = ((np.arange(out_w)[None, :] // max(1, out_w // 32)) % 2) * 0.05
    img = np.clip(img.astype(np.float32) * (0.95 + sep[..., None]), 0, 255).astype(np.uint8)
    return img


def sector_thumbnail_fast(sector_bytes: bytes, width: int, height: int) -> np.ndarray:
    # page-based intensity (256 pages)
    arr = np.frombuffer(sector_bytes, dtype=np.uint8).reshape(256, 256)
    ones_per_page = _POPCOUNT[arr].sum(axis=1).astype(np.float32)  # (256,)
    mean_bit = ones_per_page / (256.0 * 8.0)  # 1=erased, 0=programmed-ish
    t_col = (1.0 - mean_bit)  # zero_ratio per page

    # sample pages to width
    xi = np.linspace(0, 255, width).astype(int)
    col = t_col[xi][None, :]  # (1,width)

    # add fixed horizontal banding so it resembles captures
    y = np.linspace(0, 1, height)[:, None]
    stripes = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 10 * y))) * 0.08  # subtle
    t = np.clip(0.10 + 0.90 * (0.85 * col + stripes), 0, 1)

    img = _mix(GREEN, YELLOW, t[..., None])
    return img


def sector_thumbnail(
    sector_bytes: bytes,
    width: int = 128,
    height: int = 32,
    bitorder: str = "msb",
    orientation: str = "horizontal",
) -> np.ndarray:
    # LOD1 uses fast thumbnailing; keep compatibility with prior signature.
    return sector_thumbnail_fast(sector_bytes, width=width, height=height)


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
    # For detailed view we want it to look paper-like:
    core_w = 256
    core = sector_band_image(sector_bytes, out_w=core_w, out_h=height, bitorder=bitorder, word_bits=256)

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
