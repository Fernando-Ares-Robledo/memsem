from core.layout import column_sector_ids_8x2


def test_column_mapping_length_and_range():
    ids = column_sector_ids_8x2(0, 0, 0)
    assert len(ids) == 16
    assert all(0 <= sid < 256 for sid in ids)


def test_column_mapping_paper_order_pattern():
    ids = column_sector_ids_8x2(0, 0, 1)
    # left side should increase 0..7, right side should decrease 15..8
    local = [sid % 32 for sid in ids]
    assert local[:8] == list(range(0, 8))
    assert local[8:] == list(range(15, 7, -1))
