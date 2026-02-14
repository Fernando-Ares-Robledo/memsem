from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.utils import parse_int


class ProgramDock(QDockWidget):
    changed = Signal(dict)
    jump_requested = Signal(int)

    def __init__(self, model, parent=None):
        super().__init__("Program / Erase", parent)
        self.model = model
        self.selected_region = {"start": 0, "size": 0x10000, "level": "sector", "sector_id": 0}
        body = QWidget()
        outer = QVBoxLayout(body)

        form = QFormLayout()
        self.unit = QComboBox()
        self.unit.addItems(["selected", "sector64", "block32", "block4", "page256", "range"])
        self.addr = QLineEdit("0x0")
        self.size = QLineEdit("0x100")
        self.seg_type = QComboBox(); self.seg_type.addItems(["fill", "hex", "text"])
        self.seg_size = QLineEdit("0x100")
        self.seg_value = QLineEdit("0xAA")
        form.addRow("Unit", self.unit)
        form.addRow("Address", self.addr)
        form.addRow("Size (range)", self.size)
        form.addRow("Segment type", self.seg_type)
        form.addRow("Segment size", self.seg_size)
        form.addRow("Segment value", self.seg_value)
        outer.addLayout(form)

        buttons = QHBoxLayout()
        b_prog = QPushButton("Program")
        b_erase = QPushButton("Erase")
        b_jump = QPushButton("Jump")
        b_prog.clicked.connect(self._program)
        b_erase.clicked.connect(self._erase)
        b_jump.clicked.connect(self._jump)
        buttons.addWidget(b_prog); buttons.addWidget(b_erase); buttons.addWidget(b_jump)
        outer.addLayout(buttons)

        self.log = QTextEdit(); self.log.setReadOnly(True)
        outer.addWidget(self.log)
        self.setWidget(body)

    def set_selected_region(self, info: dict):
        if "start" not in info or "size" not in info:
            return
        self.selected_region = dict(info)
        self.addr.setText(f"0x{info['start']:X}")
        self.size.setText(f"0x{info['size']:X}")

    def _resolve_region(self):
        u = self.unit.currentText()
        if u == "selected":
            return self.selected_region["start"], self.selected_region["size"]
        addr = parse_int(self.addr.text())
        if u == "sector64":
            start = (addr >> 16) << 16; size = 0x10000
        elif u == "block32":
            start = (addr >> 15) << 15; size = 0x8000
        elif u == "block4":
            start = (addr >> 12) << 12; size = 0x1000
        elif u == "page256":
            start = (addr >> 8) << 8; size = 0x100
        else:
            start = addr; size = parse_int(self.size.text())
        return start, size

    def _program(self):
        start, size = self._resolve_region()
        seg = {"type": self.seg_type.currentText(), "size_bytes": parse_int(self.seg_size.text()), "value": self.seg_value.text()}
        self.model.program(start, size, [seg], enforce_nor=True)
        self.log.append(f"Programmed 0x{start:X} size 0x{size:X}")
        self.changed.emit({"start": start, "size": size})

    def _erase(self):
        start, size = self._resolve_region()
        self.model.erase(start, size)
        self.log.append(f"Erased 0x{start:X} size 0x{size:X}")
        self.changed.emit({"start": start, "size": size})

    def _jump(self):
        self.jump_requested.emit(parse_int(self.addr.text()))
