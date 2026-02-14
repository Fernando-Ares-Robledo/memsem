from core.addressing import page_range, sector_range, sub4_range, sub32_range


def test_address_ranges():
    assert sector_range(0) == (0x000000, 0x00FFFF)
    assert sector_range(511) == (0x01FF0000, 0x01FFFFFF)

    assert sub32_range(0) == (0x000000, 0x007FFF)
    assert sub32_range(1023) == (0x01FF8000, 0x01FFFFFF)

    assert sub4_range(0) == (0x000000, 0x000FFF)
    assert sub4_range(8191) == (0x01FFF000, 0x01FFFFFF)

    assert page_range(0) == (0x000000, 0x0000FF)
    assert page_range(131071) == (0x01FFFF00, 0x01FFFFFF)
