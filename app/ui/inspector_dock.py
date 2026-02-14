from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QLabel, QTextEdit, QVBoxLayout, QWidget

from core.addressing import dataset_address
from core.ecc_overlay import ecc_for_dataset


class InspectorDock(QDockWidget):
    def __init__(self, model, parent=None):
        super().__init__("Inspector", parent)
        self.model = model
        body = QWidget()
        lay = QVBoxLayout(body)
        self.sel_label = QLabel("Selection: none")
        self.hex_view = QTextEdit()
        self.hex_view.setReadOnly(True)
        self.ecc_view = QTextEdit()
        self.ecc_view.setReadOnly(True)
        lay.addWidget(self.sel_label)
        lay.addWidget(self.hex_view)
        lay.addWidget(QLabel("ECC inspector (datasets 0..15):"))
        lay.addWidget(self.ecc_view)
        self.setWidget(body)

    def update_for_sector(self, sector_id: int):
        self.sel_label.setText(f"Selection: sector {sector_id}")
        start = sector_id * 0x10000
        sample = self.model.read(start, 32)
        hexs = " ".join(f"{b:02X}" for b in sample)
        ascii_txt = "".join(chr(b) if 32 <= b < 127 else "." for b in sample)
        self.hex_view.setPlainText(f"addr 0x{start:06X}:\n{hexs}\n{ascii_txt}")

        lines = []
        for p in range(16):
            ds_start, _ = dataset_address(sector_id, p)
            bits = ecc_for_dataset(self.model.read(ds_start, 0x100))
            lines.append(f"{p:03d}: {''.join(str(int(x)) for x in bits)}")
        self.ecc_view.setPlainText("\n".join(lines))
