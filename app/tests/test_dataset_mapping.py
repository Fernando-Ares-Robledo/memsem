from core.addressing import dataset_address


def test_dataset_page_mapping():
    s = 10
    p = 25
    start, end = dataset_address(s, p)
    assert start == s * 0x10000 + p * 0x100
    assert end == start + 0xFF
