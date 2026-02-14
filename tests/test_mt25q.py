from memsem.models import mt25q


def test_mt25q_formulas():
    assert mt25q.range_for_sector(0) == (0x000000, 0x00FFFF)
    assert mt25q.range_for_sector(511) == (0x01FF0000, 0x01FFFFFF)
    assert mt25q.range_for_sub32(1023) == (0x01FF8000, 0x01FFFFFF)
    assert mt25q.range_for_sub4(8191) == (0x01FFF000, 0x01FFFFFF)
    assert mt25q.range_for_page(1) == (0x100, 0x1FF)
    assert mt25q.sector_segment(255) == 0
    assert mt25q.sector_segment(256) == 1
