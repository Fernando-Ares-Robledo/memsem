from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.patterns import Segment


class PatternEditor(QWidget):
    apply_to_sector = Signal(list)
    apply_to_sub4 = Signal(list)
    nor_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)

        self.seg_boxes = []
        for idx in range(2):
            box = QGroupBox(f"Segment {idx + 1}")
            form = QFormLayout(box)
            size_kb = QSpinBox()
            size_kb.setRange(0, 32768)
            size_kb.setValue(128 if idx == 0 else 0)
            kind = QComboBox()
            kind.addItems(["text", "hex", "fill"])
            value = QLineEdit("D" if idx == 0 else "")
            form.addRow("Size KB", size_kb)
            form.addRow("Type", kind)
            form.addRow("Value", value)
            self.seg_boxes.append((size_kb, kind, value))
            root.addWidget(box)

        self.nor_box = QCheckBox("Enforce NOR programming (new = old & data)")
        self.nor_box.toggled.connect(self.nor_toggled.emit)
        root.addWidget(self.nor_box)

        h = QHBoxLayout()
        self.apply_sector = QPushButton("Program selected sector")
        self.apply_sub4 = QPushButton("Program selected 4KB block")
        self.apply_sector.clicked.connect(lambda: self.apply_to_sector.emit(self.current_segments()))
        self.apply_sub4.clicked.connect(lambda: self.apply_to_sub4.emit(self.current_segments()))
        h.addWidget(self.apply_sector)
        h.addWidget(self.apply_sub4)
        root.addLayout(h)

        root.addStretch(1)

    def current_segments(self) -> list[Segment]:
        segments = []
        for size, kind, value in self.seg_boxes:
            if size.value() <= 0:
                continue
            val: str | int = value.text()
            if kind.currentText() == "fill":
                text = value.text().strip().lower()
                if text.startswith("0x"):
                    val = int(text, 16)
                else:
                    val = int(text or "0")
            segments.append(Segment(size.value(), kind.currentText(), val))
        return segments
