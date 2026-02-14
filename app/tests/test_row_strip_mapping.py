from core.layout import row_sector_ids, row_strip_order


def test_row_sector_ids_len_and_bounds():
    ids = row_sector_ids(0, 0)
    assert len(ids) == 16
    assert all(0 <= s < 256 for s in ids)


def test_row_strip_mirror_order():
    left, right = row_strip_order(1, 9)
    assert len(left) == 8
    assert len(right) == 8
    raw = row_sector_ids(1, 9)
    assert left == raw[:8]
    assert right == list(reversed(raw[8:]))
