from core.model import MemoryModel


def test_program_erase_nor_rule():
    m = MemoryModel(enforce_nor=True)
    m.program(0x100, 4, [{"type": "fill", "size_bytes": 4, "value": 0x0F}])
    assert m.read(0x100, 4) == b"\x0F" * 4
    m.program(0x100, 4, [{"type": "fill", "size_bytes": 4, "value": 0xF0}])
    assert m.read(0x100, 4) == b"\x00" * 4
    m.erase(0x100, 4)
    assert m.read(0x100, 4) == b"\xFF" * 4
