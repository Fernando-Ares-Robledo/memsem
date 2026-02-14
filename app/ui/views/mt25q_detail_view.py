from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from app.core.mapping import sector_address_range


class MT25QDetailView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.header = QLabel("Sector details")
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.header)
        layout.addWidget(self.text)

    def set_sector(self, sector_id: int):
        start, end = sector_address_range(sector_id)
        lines = [
            f"Sector {sector_id}",
            f"Address: 0x{start:08X} - 0x{end:08X}",
            "32KB offsets: 0x0000, 0x8000",
            "4KB offsets: " + ", ".join(f"0x{x:04X}" for x in range(0, 0x10000, 0x1000)),
            "Page offsets: 0x0000..0xFF00 step 0x100",
        ]
        self.text.setPlainText("\n".join(lines))
