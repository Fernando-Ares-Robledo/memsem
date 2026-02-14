from core.layout import folded64_local_to_cell


def test_folded64_mapping_exact_table():
    assert folded64_local_to_cell(48) == (0, 0)
    assert folded64_local_to_cell(32) == (0, 1)
    assert folded64_local_to_cell(16) == (0, 2)
    assert folded64_local_to_cell(0) == (0, 3)

    assert folded64_local_to_cell(55) == (7, 0)
    assert folded64_local_to_cell(39) == (7, 1)
    assert folded64_local_to_cell(23) == (7, 2)
    assert folded64_local_to_cell(7) == (7, 3)

    assert folded64_local_to_cell(63) == (9, 0)
    assert folded64_local_to_cell(47) == (9, 1)
    assert folded64_local_to_cell(31) == (9, 2)
    assert folded64_local_to_cell(15) == (9, 3)

    assert folded64_local_to_cell(56) == (16, 0)
    assert folded64_local_to_cell(40) == (16, 1)
    assert folded64_local_to_cell(24) == (16, 2)
    assert folded64_local_to_cell(8) == (16, 3)
