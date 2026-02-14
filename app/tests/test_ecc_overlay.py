from core.ecc_overlay import ecc_for_dataset


def test_ecc_deterministic():
    d = bytes([0xAA] * 0x100)
    e1 = ecc_for_dataset(d)
    e2 = ecc_for_dataset(d)
    assert e1.tolist() == e2.tolist()
    assert len(e1) == 10
