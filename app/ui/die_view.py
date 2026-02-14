from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsView

from core.addressing import SECTOR_SIZE, sector_start
from core.layout import sector_grid_position
from core.render import sector_detailed_image, sector_state_summary, sector_thumbnail


@dataclass
class Selection:
    level: str
    sector_id: int | None = None
    page_id: int | None = None
    bit_index: int | None = None


class SectorItem(QGraphicsRectItem):
    def __init__(self, sector_id: int, rect, parent=None):
        super().__init__(rect, parent)
        self.sector_id = sector_id
        self.setPen(QPen(QColor(60, 90, 60), 0.5))


class DieView(QGraphicsView):
    selection_changed = Signal(dict)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self._items = {}
        self.bitorder = "msb"
        self.show_ecc = True
        self._selection = Selection(level="die")
        self._build_scene()

    def _build_scene(self):
        self.scene.clear()
        cell_w, cell_h = 44, 30
        gap = 8
        array_h = 17 * (cell_h + 2)
        strip_h = 70
        self.scene.addRect(0, array_h + gap, 16 * (cell_w + 2), strip_h, QPen(Qt.NoPen), QBrush(QColor(40, 50, 45)))

        for sector_id in range(512):
            array_idx, row, col = sector_grid_position(sector_id)
            x = col * (cell_w + 2)
            y_base = 0 if array_idx == 0 else array_h + strip_h + 2 * gap
            y = y_base + row * (cell_h + 2)
            item = SectorItem(sector_id, (0, 0, cell_w, cell_h))
            item.setPos(x, y)
            self.scene.addItem(item)
            self._items[sector_id] = item
        self.refresh_visible()

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        self.refresh_visible()

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, SectorItem):
            self._selection = Selection(level="sector", sector_id=item.sector_id)
            self.selection_changed.emit({"level": "sector", "sector_id": item.sector_id})
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, SectorItem):
            self.zoom_to_sector(item.sector_id)
        super().mouseDoubleClickEvent(event)

    def zoom_to_sector(self, sector_id: int):
        rect = self._items[sector_id].sceneBoundingRect()
        self.fitInView(rect.adjusted(-10, -10, 10, 10), Qt.KeepAspectRatio)

    def rotate_quadrant(self, deg: int):
        self.resetTransform()
        self.rotate(deg)

    def refresh_visible(self):
        scale = self.transform().m11()
        for sector_id, item in self._items.items():
            start = sector_start(sector_id)
            sbytes = self.model.read(start, SECTOR_SIZE)
            if scale < 0.45:
                erased, ratio = sector_state_summary(sbytes)
                c = QColor(70, 140, 70) if erased else QColor(120 + int(120 * ratio), 170, 70)
                item.setBrush(QBrush(c))
            elif scale < 2.0:
                arr = sector_thumbnail(sbytes, width=24, height=16, bitorder=self.bitorder)
                item.setBrush(QBrush(self._pixmap_brush(arr)))
            else:
                arr = sector_detailed_image(sbytes, height=30, with_ecc=False, bitorder=self.bitorder)
                item.setBrush(QBrush(self._pixmap_brush(arr)))

    def _pixmap_brush(self, arr: np.ndarray) -> QPixmap:
        h, w, _ = arr.shape
        img = QImage(arr.data, w, h, 3 * w, QImage.Format_RGB888)
        return QPixmap.fromImage(img.copy())

