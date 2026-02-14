from core.layout import folded64_cell


def test_folded64_key_positions():
    assert folded64_cell(0).row == 0 and folded64_cell(0).col == 3
    assert folded64_cell(48).row == 0 and folded64_cell(48).col == 0
    assert folded64_cell(7).row == 7 and folded64_cell(7).col == 3
    assert folded64_cell(15).row == 9 and folded64_cell(15).col == 3
    assert folded64_cell(8).row == 16 and folded64_cell(8).col == 3
    assert folded64_cell(63).row == 9 and folded64_cell(63).col == 0
