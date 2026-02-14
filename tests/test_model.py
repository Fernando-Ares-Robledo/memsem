from core.constants import SUBSECTOR_SIZE_4K
from core.model import FlashModel


def test_nor_program_rule():
    m = FlashModel()
    m.data[0] = 0x0F
    m.program(0, bytes([0xF0]), enforce_nor_rule=True)
    assert int(m.data[0]) == 0x00


def test_program_4k_changes_only_region_and_summary():
    m = FlashModel()
    start = 0x2000
    before_other = m.get_bytes(0, 0x1000)
    payload = bytes([0x00]) * SUBSECTOR_SIZE_4K
    m.program(start, payload)

    assert m.summary_ratio_non_ff(start, SUBSECTOR_SIZE_4K) == 1.0
    assert m.get_bytes(0, 0x1000) == before_other
