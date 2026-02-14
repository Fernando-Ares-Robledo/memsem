from core.render import sector_detailed_image


def test_vertical_orientation_is_tall_and_narrow():
    data = bytes([0xAA]) * 0x10000
    h = sector_detailed_image(data, height=240, with_ecc=False, orientation="horizontal")
    v = sector_detailed_image(data, height=240, with_ecc=False, orientation="vertical")
    assert h.shape[0] == 240
    assert h.shape[1] == 256
    assert v.shape[0] == 240
    assert v.shape[1] == 268
