from core.addressing import page_region, sector_region, sub4_region, sub32_region


def test_addressing_formulas():
    addr = 0x012345
    s = sector_region(addr)
    assert s.unit_id == addr >> 16
    assert s.start == (addr >> 16) * 0x10000
    assert s.end == s.start + 0xFFFF

    b32 = sub32_region(addr)
    assert b32.start == (addr >> 15) * 0x8000
    assert b32.end == b32.start + 0x7FFF

    b4 = sub4_region(addr)
    assert b4.start == (addr >> 12) * 0x1000
    assert b4.end == b4.start + 0xFFF

    p = page_region(addr)
    assert p.start == (addr >> 8) * 0x100
    assert p.end == p.start + 0xFF
