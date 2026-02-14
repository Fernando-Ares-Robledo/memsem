"""Deterministic simulated ECC overlay bits."""

from __future__ import annotations

import numpy as np


ECC_BITS = 10
SEC_BITS = 9


def ecc_for_dataset(dataset_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(dataset_bytes, dtype=np.uint8)
    bits = np.unpackbits(arr)
    sec = np.zeros(SEC_BITS, dtype=np.uint8)
    idx = np.arange(bits.size)
    for k in range(SEC_BITS):
        sec[k] = np.bitwise_xor.reduce(bits[idx % SEC_BITS == k]) if bits.size else 0
    ded = (np.bitwise_xor.reduce(bits) if bits.size else 0) ^ np.bitwise_xor.reduce(sec)
    return np.concatenate([[ded], sec]).astype(np.uint8)


def ecc_matrix_for_sector(sector_bytes: bytes) -> np.ndarray:
    if len(sector_bytes) != 0x10000:
        raise ValueError("sector_bytes must be 64KiB")
    matrix = np.zeros((ECC_BITS, 256), dtype=np.uint8)
    for page in range(256):
        start = page * 0x100
        matrix[:, page] = ecc_for_dataset(sector_bytes[start : start + 0x100])
    return matrix
