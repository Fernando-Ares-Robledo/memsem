from core.addressing import SECTOR_SIZE, sector_start
from core.model import MemoryModel
from core.preset import apply_paper_like_preset, validate_paper_like_hashes


def test_paper_like_preset_programs_expected_ranges():
    m = MemoryModel()
    apply_paper_like_preset(m)

    assert m.read(sector_start(0), 4) == b"DDDD"
    assert m.read(sector_start(9), 16) == b"\x00" * 16
    assert m.read(sector_start(14), 16) == b"\x55" * 16
    assert m.read(sector_start(15), 16) == b"\xAA" * 16

    s6 = m.read(sector_start(6), SECTOR_SIZE)
    assert s6[0x8000:] == b"\xFF" * 0x8000


def test_paper_like_hash_validation_pairs_match():
    m = MemoryModel()
    apply_paper_like_preset(m)
    _, results = validate_paper_like_hashes(m)
    assert all(r.match for r in results)
