from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsView


@dataclass
class TileInfo:
    granularity: str
    tile_id: int
    start: int
    end: int


class TileItem(QGraphicsRectItem):
    def __init__(self, _rect, info: TileInfo, cb: Callable[[TileInfo], float]):
        super().__init__()
        self.info = info
        ratio = max(0.0, min(1.0, cb(info)))
        color = QColor.fromHsvF(0.32 - ratio * 0.32, 0.75, 0.5 + ratio * 0.45)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 0.5))
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)


class DieView(QGraphicsView):
    tile_selected = Signal(object)
    tile_drilled = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._zoom = 1.0

    def wheelEvent(self, event):
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        self._zoom *= factor
        self.scale(factor, factor)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if isinstance(item, TileItem):
            self.tile_drilled.emit(item.info)
        return super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if isinstance(item, TileItem):
            self.tile_selected.emit(item.info)
        return super().mousePressEvent(event)

    def render_layout(
        self,
        labels: list[list[int | None]],
        granularity: str,
        address_for_id: Callable[[int], tuple[int, int]],
        ratio_for_tile: Callable[[TileInfo], float],
    ):
        self.scene.clear()
        tile_w, tile_h = 38, 22
        gap = 4
        for r, row in enumerate(labels):
            for c, val in enumerate(row):
                x = c * (tile_w + gap)
                y = r * (tile_h + gap)
                if val is None:
                    deco = self.scene.addRect(x, y, tile_w, tile_h, QPen(Qt.NoPen), QBrush(QColor(48, 48, 48)))
                    deco.setToolTip("Periphery / logic")
                    continue
                start, end = address_for_id(val)
                info = TileInfo(granularity, val, start, end)
                item = TileItem(None, info, ratio_for_tile)
                item.setRect(x, y, tile_w, tile_h)
                self.scene.addItem(item)
        self._draw_periphery(labels, tile_w, tile_h, gap)
        self.scene.setSceneRect(self.scene.itemsBoundingRect())

    def _draw_periphery(self, labels, tile_w, tile_h, gap):
        rows = len(labels)
        cols = max((len(r) for r in labels), default=0)
        total_w = cols * (tile_w + gap)
        total_h = rows * (tile_h + gap)
        self.scene.addRect(-20, 0, 12, total_h, QPen(Qt.NoPen), QBrush(QColor(90, 70, 110, 120)))
        self.scene.addRect(total_w + 6, 0, 12, total_h, QPen(Qt.NoPen), QBrush(QColor(90, 70, 110, 120)))
        self.scene.addRect(0, total_h / 2 - 12, total_w, 24, QPen(Qt.NoPen), QBrush(QColor(120, 80, 80, 90)))
