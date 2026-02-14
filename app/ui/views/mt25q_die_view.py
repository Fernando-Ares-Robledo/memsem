from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QBrush, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QVBoxLayout, QWidget

from app.core.mapping import grid_to_mt25q_sector, mt25q_sector_to_grid
from app.core.mt25q_model import MT25QModel
from app.core.rendering import color_for_density
from .common import ZoomableGraphicsView


class MT25QDieView(QWidget):
    sector_selected = Signal(int)

    def __init__(self, model: MT25QModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.size = 26
        self.scene = QGraphicsScene(self)
        self.view = ZoomableGraphicsView()
        self.view.setScene(self.scene)
        self.view.mousePressEvent = self._mouse_press
        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        self.refresh()

    def refresh(self):
        self.scene.clear()
        periphery_h = 30
        self.scene.addRect(0, 16 * self.size + 10, 16 * self.size, periphery_h, QPen(), QBrush())
        for bank in range(2):
            y0 = bank * (16 * self.size + periphery_h + 20)
            for row in range(16):
                for col in range(16):
                    sid = grid_to_mt25q_sector(bank, row, col)
                    _, density = self.model.sector_state(sid)
                    rect = QGraphicsRectItem(col * self.size, y0 + row * self.size, self.size - 2, self.size - 2)
                    rect.setBrush(QBrush(color_for_density(density)))
                    rect.setPen(QPen())
                    rect.setData(0, sid)
                    self.scene.addItem(rect)

                    # visual super-block boundary (4x4)
                    if row % 4 == 0:
                        self.scene.addLine(col * self.size, y0 + row * self.size, col * self.size + self.size, y0 + row * self.size)
                    if col % 4 == 0:
                        self.scene.addLine(col * self.size, y0 + row * self.size, col * self.size, y0 + row * self.size + self.size)

    def _mouse_press(self, event):
        pos = self.view.mapToScene(event.position().toPoint())
        item = self.scene.itemAt(pos, self.view.transform())
        if item is not None and item.data(0) is not None:
            self.sector_selected.emit(int(item.data(0)))
        ZoomableGraphicsView.mousePressEvent(self.view, event)
