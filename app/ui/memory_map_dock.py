from PySide6.QtWidgets import QDockWidget, QTextEdit


class MemoryMapDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Memory Map", parent)
        t = QTextEdit()
        t.setReadOnly(True)
        t.setPlainText(
            "32MiB model, range 0x000000..0x01FFFFFF\n\n"
            "64KB sector:\n"
            "sector_id = addr >> 16\nstart = sector_id * 0x10000\nend = start + 0xFFFF\n\n"
            "32KB block:\n"
            "sub32_id = addr >> 15\nstart = sub32_id * 0x8000\nend = start + 0x7FFF\n\n"
            "4KB block:\n"
            "sub4_id = addr >> 12\nstart = sub4_id * 0x1000\nend = start + 0xFFF\n\n"
            "256B page:\n"
            "page_id = addr >> 8\nstart = page_id * 0x100\nend = start + 0xFF\n"
        )
        self.setWidget(t)
