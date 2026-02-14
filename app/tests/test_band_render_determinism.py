from core.render import sector_thumbnail, thumbnail_hash


def test_thumbnail_determinism():
    data = bytes([i % 251 for i in range(0x10000)])
    h1 = thumbnail_hash(sector_thumbnail(data, width=64, height=24, bitorder="msb"))
    h2 = thumbnail_hash(sector_thumbnail(data, width=64, height=24, bitorder="msb"))
    assert h1 == h2
