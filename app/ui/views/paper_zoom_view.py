from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QHBoxLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.paper_model import PaperModel
from app.core.rendering import RenderColors, render_band_tile_image
from .common import ZoomableGraphicsView


class PaperZoomView(QWidget):
    selection_changed = Signal(dict)

    def __init__(self, model: PaperModel, colors: RenderColors, parent=None):
        super().__init__(parent)
        self.model = model
        self.colors = colors
        self.cell = 8

        root = QVBoxLayout(self)
        controls = QFormLayout()
        self.sector = QSpinBox(); self.sector.setRange(0, 15)
        self.band = QSpinBox(); self.band.setRange(0, 255)
        self.cstart = QSpinBox(); self.cstart.setRange(0, 255)
        self.cwidth = QSpinBox(); self.cwidth.setRange(1, 256); self.cwidth.setValue(256)
        self.grid = QCheckBox("Grid")
        for w in (self.sector, self.band, self.cstart, self.cwidth):
            w.valueChanged.connect(self.refresh)
        self.grid.toggled.connect(self.refresh)
        controls.addRow("Sector", self.sector)
        controls.addRow("Band", self.band)
        controls.addRow("Crop start", self.cstart)
        controls.addRow("Crop width", self.cwidth)
        controls.addRow("Overlay", self.grid)
        root.addLayout(controls)

        self.view = ZoomableGraphicsView()
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        root.addWidget(self.view)
        self.pix_item: QGraphicsPixmapItem | None = None
        self.cross: QGraphicsRectItem | None = None
        self.view.mousePressEvent = self._mouse_press
        self.refresh()

    def _mouse_press(self, event):
        pos = self.view.mapToScene(event.position().toPoint())
        col = int(pos.x() // self.cell)
        row = int(pos.y() // self.cell)
        if 0 <= row < 16 and 0 <= col < self.cwidth.value():
            if self.cross:
                self.scene.removeItem(self.cross)
            self.cross = self.scene.addRect(col * self.cell, row * self.cell, self.cell, self.cell, QPen(Qt.GlobalColor.red, 2))
            real_col = self.cstart.value() + col
            word = self.model.selected_word_bytes(self.sector.value(), row, real_col)
            bits = self.model.sector_words_bits(self.sector.value())[row * 256 + real_col]
            payload = {
                "sector": self.sector.value(), "band": self.band.value(), "row": row, "col": real_col,
                "bit": int(bits[self.band.value()]),
                "word_hex": word.tobytes().hex(" "),
                "ascii": "".join(chr(b) if 32 <= b <= 126 else "." for b in word.tolist()),
                "bit_grid": "\n".join("".join(str(int(v)) for v in bits[i:i+16]) for i in range(0, 256, 16)),
            }
            self.selection_changed.emit(payload)
        ZoomableGraphicsView.mousePressEvent(self.view, event)

    def refresh(self):
        width = min(self.cwidth.value(), 256 - self.cstart.value())
        tile = self.model.band_tile(self.sector.value(), self.band.value(), self.cstart.value(), width)
        qimg = render_band_tile_image(tile, self.colors, self.cell)
        pix = QPixmap.fromImage(qimg)
        self.scene.clear()
        self.pix_item = self.scene.addPixmap(pix)
        if self.grid.isChecked():
            pen = QPen(Qt.GlobalColor.black, 0.4)
            for r in range(17):
                self.scene.addLine(0, r * self.cell, width * self.cell, r * self.cell, pen)
            for c in range(width + 1):
                self.scene.addLine(c * self.cell, 0, c * self.cell, 16 * self.cell, pen)
