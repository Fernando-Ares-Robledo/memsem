from app.core.mapping import (
    page_address_range,
    sector_address_range,
    sub32_address_range,
    sub4_address_range,
)
from app.core.mt25q_model import MT25QModel
from app.core.patterns import Segment


def test_sector_formulas():
    assert sector_address_range(0) == (0x000000, 0x00FFFF)
    assert sector_address_range(255) == (0xFF0000, 0xFFFFFF)
    assert sector_address_range(256) == (0x01000000, 0x0100FFFF)
    assert sector_address_range(511) == (0x01FF0000, 0x01FFFFFF)


def test_subsector_and_page_formulas():
    assert sub4_address_range(0) == (0x000000, 0x000FFF)
    assert sub4_address_range(8191) == (0x01FFF000, 0x01FFFFFF)
    assert sub32_address_range(0) == (0x000000, 0x007FFF)
    assert sub32_address_range(1023) == (0x01FF8000, 0x01FFFFFF)
    assert page_address_range(0) == (0x0, 0xFF)
    assert page_address_range(131071) == (0x01FFFF00, 0x01FFFFFF)


def test_nor_rule_programming():
    model = MT25QModel()
    model.memory[0] = 0x0F
    model.set_nor_enforced(True)
    model.program(0, 1, [Segment(1, "fill", 0xF0)])
    assert model.memory[0] == 0x00
