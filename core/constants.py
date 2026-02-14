from dataclasses import dataclass

TOTAL_BYTES = 32 * 1024 * 1024
MAX_ADDRESS = TOTAL_BYTES - 1

SECTOR_SIZE_64K = 0x10000
SUBSECTOR_SIZE_32K = 0x8000
SUBSECTOR_SIZE_4K = 0x1000
PAGE_SIZE = 0x100

SECTORS_TOTAL = TOTAL_BYTES // SECTOR_SIZE_64K
SUBSECTORS_32K_TOTAL = TOTAL_BYTES // SUBSECTOR_SIZE_32K
SUBSECTORS_4K_TOTAL = TOTAL_BYTES // SUBSECTOR_SIZE_4K
PAGES_TOTAL = TOTAL_BYTES // PAGE_SIZE


@dataclass
class LayoutConfig:
    number_of_blocks_per_bank: int = 4
    block_width_in_cells: int = 4
    block_height_in_cells: int = 17
    gap_height_px: int = 40
    hide_blocks_bank0: list[int] | None = None
    hide_blocks_bank1: list[int] | None = None
    show_sectors_per_bank: int | None = None

    def __post_init__(self) -> None:
        self.hide_blocks_bank0 = self.hide_blocks_bank0 or []
        self.hide_blocks_bank1 = self.hide_blocks_bank1 or []
