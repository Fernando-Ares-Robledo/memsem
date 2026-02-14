from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.model import FlashModel, Selection


class InspectorWidget(QWidget):
    def __init__(self, model: FlashModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.selection: Selection | None = None

        self.info = QLabel("No selection")
        self.word_bits = QSpinBox()
        self.word_bits.setRange(8, 4096)
        self.word_bits.setValue(256)
        self.plane = QSpinBox()
        self.plane.setRange(0, 255)
        self.bitorder = QCheckBox("MSB first")
        self.bitorder.setChecked(True)

        self.grid = QTableWidget(0, 0)
        self.grid.cellClicked.connect(self._on_click)
        self.hex_preview = QPlainTextEdit()
        self.hex_preview.setReadOnly(True)

        controls = QFormLayout()
        controls.addRow("Word bits", self.word_bits)
        controls.addRow("Plane", self.plane)
        controls.addRow("Bit order", self.bitorder)
        bar = QHBoxLayout()
        bar.addLayout(controls)

        layout = QVBoxLayout(self)
        layout.addWidget(self.info)
        layout.addLayout(bar)
        layout.addWidget(self.grid)
        layout.addWidget(self.hex_preview)

        self.word_bits.valueChanged.connect(self.refresh)
        self.plane.valueChanged.connect(self.refresh)
        self.bitorder.stateChanged.connect(self.refresh)

    def set_selection(self, sel: Selection) -> None:
        self.selection = sel
        self.info.setText(f"{sel.level}: 0x{sel.start:06X}..0x{sel.end:06X} ({sel.size} bytes)")
        self.refresh()

    def refresh(self) -> None:
        if not self.selection:
            return
        wb = self.word_bits.value()
        self.plane.setMaximum(wb - 1)
        vec = self.model.bit_plane(
            self.selection.start,
            self.selection.size,
            word_bits=wb,
            plane=self.plane.value(),
            msb_first=self.bitorder.isChecked(),
        )
        if vec.size == 0:
            self.grid.setRowCount(0)
            self.grid.setColumnCount(0)
            return
        cols = 64
        rows = int(np.ceil(len(vec) / cols))
        self.grid.setRowCount(rows)
        self.grid.setColumnCount(cols)
        for i, b in enumerate(vec):
            r, c = divmod(i, cols)
            it = QTableWidgetItem(str(int(b)))
            it.setTextAlignment(Qt.AlignCenter)
            self.grid.setItem(r, c, it)
        preview = self.model.get_bytes(self.selection.start, min(64, self.selection.size))
        ascii_ = ''.join(chr(x) if 32 <= x <= 126 else '.' for x in preview)
        self.hex_preview.setPlainText(' '.join(f"{x:02X}" for x in preview) + "\n" + ascii_)

    def _on_click(self, row: int, col: int) -> None:
        if not self.selection:
            return
        idx = row * self.grid.columnCount() + col
        bit_offset = idx * self.word_bits.value() + self.plane.value()
        byte_addr = self.selection.start + bit_offset // 8
        bit_idx = bit_offset % 8
        if byte_addr > self.selection.end:
            return
        value = (self.model.data[byte_addr] >> (7 - bit_idx)) & 1
        self.info.setText(
            f"addr=0x{byte_addr:06X} bit={bit_idx} value={int(value)} range=0x{self.selection.start:06X}-0x{self.selection.end:06X}"
        )
