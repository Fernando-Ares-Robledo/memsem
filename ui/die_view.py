from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView

from core.constants import LayoutConfig, PAGE_SIZE, SECTOR_SIZE_64K, SUBSECTOR_SIZE_4K, SUBSECTOR_SIZE_32K
from core.layout import iter_visible_sectors
from core.model import FlashModel, Selection


class Tile(QGraphicsRectItem):
    def __init__(self, kind: str, idx: int, start: int, size: int, x: float, y: float, w: float, h: float):
        super().__init__(x, y, w, h)
        self.kind = kind
        self.idx = idx
        self.start = start
        self.size = size
        self.setPen(QPen(Qt.black, 0.6))


@dataclass
class TileSummary:
    sector_id: int
    ratio: float


class SummaryWorkerSignals(QObject):
    done = Signal(object)


class SummaryWorker(QRunnable):
    def __init__(self, model: FlashModel, sector_ids: list[int], signals: SummaryWorkerSignals):
        super().__init__()
        self.model = model
        self.sector_ids = sector_ids
        self.signals = signals

    def run(self):
        out = []
        for sid in self.sector_ids:
            start = sid * SECTOR_SIZE_64K
            region = self.model.data[start : start + SECTOR_SIZE_64K]
            ratio = float(np.count_nonzero(region != 0xFF)) / float(SECTOR_SIZE_64K)
            out.append(TileSummary(sid, ratio))
        self.signals.done.emit(out)


class DieView(QGraphicsView):
    selection_changed = Signal(object)

    def __init__(self, model: FlashModel, parent: QObject | None = None):
        super().__init__(parent)
        self.model = model
        self.scene_ = QGraphicsScene(self)
        self.setScene(self.scene_)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.scale_factor = 1.0
        self.rotation_deg = 0
        self.cell = 26
        self.gap = 6
        self.tiles: list[Tile] = []
        self.ratio_cache: dict[int, float] = {}
        self.pool = QThreadPool.globalInstance()
        self.mode = "overview"
        self.current: Selection | None = None
        self.rebuild_scene()

    def rebuild_scene(self) -> None:
        if self.mode == "overview":
            self._draw_overview()
            self.refresh_summaries_async()
        else:
            self._draw_detail()

    def _clear(self):
        self.scene_.clear()
        self.tiles.clear()

    def _draw_overview(self):
        self._clear()
        cfg: LayoutConfig = self.model.layout
        placements = iter_visible_sectors(cfg)
        for p in placements:
            x = p.x * (self.cell + self.gap)
            y = p.y * (self.cell + self.gap)
            t = Tile("sector64", p.sector_id, p.sector_id * SECTOR_SIZE_64K, SECTOR_SIZE_64K, x, y, self.cell, self.cell)
            t.setBrush(QColor(245, 245, 245))
            self.scene_.addItem(t)
            self.tiles.append(t)
        self.scene_.setSceneRect(self.scene_.itemsBoundingRect().adjusted(-40, -40, 40, 40))

    def _draw_detail(self):
        self._clear()
        if not self.current:
            return
        base = self.current.start
        if self.current.level == "sector64":
            # 2 halves + 16 sub4 blocks
            for i in range(2):
                t = Tile("sub32", i, base + i * SUBSECTOR_SIZE_32K, SUBSECTOR_SIZE_32K, 20 + i * 220, 20, 200, 70)
                ratio = self.model.summary_ratio_non_ff(t.start, t.size)
                shade = int(245 - ratio * 180)
                t.setBrush(QColor(shade, shade, 255))
                self.scene_.addItem(t); self.tiles.append(t)
            for i in range(16):
                r, c = divmod(i, 4)
                start = base + i * SUBSECTOR_SIZE_4K
                t = Tile("sub4", i, start, SUBSECTOR_SIZE_4K, 20 + c * 105, 120 + r * 65, 95, 55)
                ratio = self.model.summary_ratio_non_ff(t.start, t.size)
                shade = int(245 - ratio * 180)
                t.setBrush(QColor(255, shade, shade))
                self.scene_.addItem(t); self.tiles.append(t)
        elif self.current.level == "sub4":
            for i in range(16):
                r, c = divmod(i, 4)
                start = base + i * PAGE_SIZE
                t = Tile("page", i, start, PAGE_SIZE, 20 + c * 110, 20 + r * 80, 100, 70)
                ratio = self.model.summary_ratio_non_ff(t.start, t.size)
                shade = int(245 - ratio * 180)
                t.setBrush(QColor(shade, 255, shade))
                self.scene_.addItem(t); self.tiles.append(t)
        elif self.current.level == "page":
            b = self.model.get_bytes(base, PAGE_SIZE)
            bits = np.unpackbits(np.frombuffer(b, dtype=np.uint8), bitorder="big")
            for i, bit in enumerate(bits[:512]):
                r, c = divmod(i, 64)
                t = Tile("bit", i, base + i // 8, 1, 10 + c * 10, 10 + r * 10, 9, 9)
                color = QColor(40, 40, 40) if bit == 0 else QColor(235, 235, 235)
                t.setBrush(color)
                self.scene_.addItem(t); self.tiles.append(t)
        back = QGraphicsSimpleTextItem("Right-click to go up / Overview")
        back.setPos(20, 420)
        self.scene_.addItem(back)
        self.scene_.setSceneRect(self.scene_.itemsBoundingRect().adjusted(-30, -30, 30, 30))

    def refresh_summaries_async(self):
        sector_ids = [t.idx for t in self.tiles if t.kind == "sector64"]
        signals = SummaryWorkerSignals()
        signals.done.connect(self._apply_summaries)
        self.pool.start(SummaryWorker(self.model, sector_ids, signals))

    def _apply_summaries(self, summaries: list[TileSummary]):
        by_id = {s.sector_id: s.ratio for s in summaries}
        for t in self.tiles:
            if t.kind != "sector64":
                continue
            ratio = by_id.get(t.idx, 0.0)
            shade = int(245 - ratio * 180)
            t.setBrush(QColor(shade, shade, shade))

    def wheelEvent(self, event):
        delta = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(delta, delta)
        self.scale_factor *= delta

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, Tile):
            sel = Selection(start=item.start, size=item.size, level=item.kind)
            self.current = sel
            self.selection_changed.emit(sel)
        elif event.button() == Qt.RightButton:
            if self.mode == "overview":
                pass
            elif self.current and self.current.level == "page":
                self.current = Selection(self.current.start - (self.current.start % SUBSECTOR_SIZE_4K), SUBSECTOR_SIZE_4K, "sub4")
            else:
                self.mode = "overview"
                self.current = None
            self.rebuild_scene()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, Tile):
            if item.kind in {"sector64", "sub4", "page"}:
                self.mode = "detail"
                self.current = Selection(item.start, item.size, item.kind)
                self.selection_changed.emit(self.current)
                self.rebuild_scene()
        super().mouseDoubleClickEvent(event)

    def set_rotation(self, deg: int) -> None:
        self.rotate(deg - self.rotation_deg)
        self.rotation_deg = deg
