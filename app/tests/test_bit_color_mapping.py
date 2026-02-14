import numpy as np

from core.render import GREEN, YELLOW, sector_thumbnail


def test_zero_and_one_bits_map_to_distinct_colors():
    img0 = sector_thumbnail(bytes([0x00]) * 0x10000, width=32, height=16)
    img1 = sector_thumbnail(bytes([0xFF]) * 0x10000, width=32, height=16)

    d0g = np.abs(img0.astype(int) - GREEN.astype(int)).sum(axis=2).mean()
    d0y = np.abs(img0.astype(int) - YELLOW.astype(int)).sum(axis=2).mean()
    d1g = np.abs(img1.astype(int) - GREEN.astype(int)).sum(axis=2).mean()
    d1y = np.abs(img1.astype(int) - YELLOW.astype(int)).sum(axis=2).mean()

    assert d0g < d0y
    assert d1y < d1g
