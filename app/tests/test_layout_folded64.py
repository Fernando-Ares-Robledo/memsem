from core.layout import folded64_cell, inverse_folded64_cell


def test_folded64_key_positions():
    assert folded64_cell(0).row == 0 and folded64_cell(0).col == 3
    assert folded64_cell(48).row == 0 and folded64_cell(48).col == 0
    assert folded64_cell(7).row == 7 and folded64_cell(7).col == 3
    assert folded64_cell(15).row == 9 and folded64_cell(15).col == 3
    assert folded64_cell(8).row == 16 and folded64_cell(8).col == 3
    assert folded64_cell(63).row == 9 and folded64_cell(63).col == 0


def test_inverse_mapping_roundtrip():
    for local_id in range(64):
        cell = folded64_cell(local_id)
        assert inverse_folded64_cell(cell.row, cell.col) == local_id
