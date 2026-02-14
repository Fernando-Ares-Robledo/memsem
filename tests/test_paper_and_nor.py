from memsem.models.paper import build_paper_preset, sector_band_bitmap, bitmap_hash
from memsem.models.flash import FlashBuffer, Region


def test_paper_preset_determinism_hashes():
    p = build_paper_preset()
    h = [bitmap_hash(sector_band_bitmap(x, 3)) for x in p.sectors]
    assert h[0] == h[12]
    assert h[7] == h[10]
    assert h[5] == h[8]


def test_nor_rule_and():
    f = FlashBuffer(1)
    f.program(Region(0,1), bytes([0x0F]), enforce_nor_rule=False)
    f.program(Region(0,1), bytes([0xF0]), enforce_nor_rule=True)
    assert f.read(Region(0,1)) == bytes([0x00])
