from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView, QMenu

from core.addressing import SECTOR_SIZE, sector_start
from core.layout import BLOCK_ROWS, GAP_ROW, SceneLayout
from core.lod_cache import LODCache
from core.render import sector_detailed_image, sector_state_summary, sector_thumbnail, sector_thumbnail_fast


@dataclass
class Selection:
    level: str
    sector_id: int
    start: int
    size: int
    sub32: int | None = None
    sub4: int | None = None


class RenderSignals(QObject):
    rendered = Signal(int, int, QPixmap)


class RenderTask(QRunnable):
    def __init__(self, sector_id: int, revision: int, lod: int, bytes_data: bytes, bitorder: str, signals: RenderSignals):
        super().__init__()
        self.sector_id = sector_id
        self.revision = revision
        self.lod = lod
        self.bytes_data = bytes_data
        self.bitorder = bitorder
        self.signals = signals

    def run(self):
        if self.lod == 1:
            arr = sector_thumbnail_fast(self.bytes_data, width=48, height=32)
        else:
            arr = sector_detailed_image(self.bytes_data, height=64, with_ecc=False, bitorder=self.bitorder)
        arr = np.ascontiguousarray(arr, dtype=np.uint8)
        h, w, _ = arr.shape
        img = QImage(arr.data, w, h, 3 * w, QImage.Format_RGB888)
        self.signals.rendered.emit(self.sector_id, self.revision, QPixmap.fromImage(img.copy()))


class SectorItem(QGraphicsRectItem):
    def __init__(self, sector_id: int, x: float, y: float, w: float, h: float, parent=None):
        super().__init__(x, y, w, h, parent)
        self.sector_id = sector_id
        self._pixmap: QPixmap | None = None
        self._selection_level: str | None = None
        self._selection_subidx: int | None = None
        self.setPen(QPen(QColor(60, 90, 60), 0.75))
        self.setBrush(QBrush(QColor(70, 140, 70)))

    def set_pixmap(self, pm: QPixmap | None):
        self._pixmap = pm
        self.update()

    def set_overlay(self, level: str | None, subidx: int | None):
        self._selection_level = level
        self._selection_subidx = subidx
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        if self._pixmap is None:
            super().paint(painter, option, widget)
        else:
            painter.drawPixmap(self.rect().toRect(), self._pixmap)
            painter.setPen(self.pen())
            painter.drawRect(self.rect())

        lod = option.levelOfDetailFromTransform(painter.worldTransform())
        if lod > 10.0:
            r = self.rect()
            painter.setPen(QPen(QColor(210, 230, 200, 120), 0.5))
            painter.drawLine(r.left(), r.top() + r.height() / 2, r.right(), r.top() + r.height() / 2)
            for i in range(1, 16):
                y = r.top() + (r.height() / 16.0) * i
                painter.drawLine(r.left(), y, r.right(), y)

        if self._selection_level == "sub32" and self._selection_subidx is not None:
            r = self.rect()
            h = r.height() / 2
            y = r.top() + (h if self._selection_subidx else 0)
            painter.fillRect(r.left(), y, r.width(), h, QColor(255, 255, 0, 70))
        elif self._selection_level == "sub4" and self._selection_subidx is not None:
            r = self.rect()
            h = r.height() / 16
            y = r.top() + self._selection_subidx * h
            painter.fillRect(r.left(), y, r.width(), h, QColor(255, 255, 0, 70))


class DieView(QGraphicsView):
    selection_changed = Signal(dict)
    row_picked = Signal(int, int)
    column_picked = Signal(int, int, int)
    stats_changed = Signal(dict)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.layout_cfg = SceneLayout()
        self._items: dict[int, SectorItem] = {}
        self._revisions = [0] * 512
        self._cache = LODCache(max_items=4096)
        self._hit = 0
        self._miss = 0
        self._queued = set()
        self.thread_pool = QThreadPool.globalInstance()
        self.signals = RenderSignals()
        self.signals.rendered.connect(self._on_rendered)

        self.bitorder = "msb"
        self.show_ecc = True
        self._selection: Selection | None = None
        self._pick_row_mode = False
        self._pick_col_mode = False
        self._build_scene()

    def _build_scene(self):
        self.scene.clear()
        cfg = self.layout_cfg
        array0_origin_y = cfg.margin
        central_strip_y = array0_origin_y + cfg.block_h + cfg.array_gap
        array1_origin_y = central_strip_y + cfg.central_strip_h + cfg.array_gap
        self.scene.addRect(cfg.margin, central_strip_y, self._array_width(cfg), cfg.central_strip_h, QPen(Qt.NoPen), QBrush(QColor(40, 50, 45)))
        for sector_id in range(512):
            x, y = self._sector_scene_xy(sector_id, cfg)
            item = SectorItem(sector_id, 0.0, 0.0, float(cfg.tile_w), float(cfg.tile_h))
            item.setPos(x, y)
            self.scene.addItem(item)
            self._items[sector_id] = item
        self.setSceneRect(0, 0, self._array_width(cfg) + cfg.margin * 2, array1_origin_y + cfg.block_h + cfg.margin)
        assert len(self._items) == 512, f"sector tiles !=512: {len(self._items)}"
        self.stats_changed.emit({"sector_items": len(self._items), "jobs": 0, "hit_rate": 0.0})
        self.refresh_visible(force=True)


    def _array_width(self, cfg: SceneLayout) -> int:
        section_w = 2 * cfg.tile_w + cfg.tile_gap
        return 8 * section_w + 7 * cfg.block_gap

    def _sector_scene_xy(self, sector_id: int, cfg: SceneLayout) -> tuple[int, int]:
        # Visual layout preset: 8 sections x 1 row per array (each section = 32 sectors)
        array_idx = 0 if sector_id < 256 else 1
        in_array = sector_id if array_idx == 0 else sector_id - 256
        section_idx = in_array // 32  # 0..7
        local = in_array % 32

        group = local // 16
        pos = local % 16
        col_in_section = 1 - group  # 2 cols within 32-sector section
        row = pos if pos < 8 else (15 - pos) + 9

        section_w = 2 * cfg.tile_w + cfg.tile_gap
        x = cfg.margin + section_idx * (section_w + cfg.block_gap) + col_in_section * (cfg.tile_w + cfg.tile_gap)

        array0_origin_y = cfg.margin
        central_strip_y = array0_origin_y + cfg.block_h + cfg.array_gap
        array1_origin_y = central_strip_y + cfg.central_strip_h + cfg.array_gap
        y_base = array0_origin_y if array_idx == 0 else array1_origin_y
        y = y_base + row * (cfg.tile_h + cfg.tile_gap)
        return x, y

    def set_row_pick_mode(self, enabled: bool):
        self._pick_row_mode = enabled

    def set_column_pick_mode(self, enabled: bool):
        self._pick_col_mode = enabled

    def wheelEvent(self, event):
        factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
        self.scale(factor, factor)
        self.refresh_visible()

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, SectorItem):
            sec_id = item.sector_id
            scene_pos = self.mapToScene(event.pos())
            local = scene_pos - item.scenePos()
            if self._pick_row_mode or self._pick_col_mode:
                array_idx, section_idx, col_in_section, row = self._section_coords(sec_id)
                if self._pick_row_mode and row != GAP_ROW:
                    self.row_picked.emit(array_idx, row)
                    self._pick_row_mode = False
                if self._pick_col_mode:
                    self.column_picked.emit(array_idx, section_idx, col_in_section)
                    self._pick_col_mode = False

            if event.button() == Qt.RightButton:
                self._show_context_menu(sec_id, local, event.globalPosition().toPoint())
                return
            self._update_selection(sec_id, local)
        super().mousePressEvent(event)


    def _section_coords(self, sector_id: int) -> tuple[int, int, int, int]:
        array_idx = 0 if sector_id < 256 else 1
        in_array = sector_id if array_idx == 0 else sector_id - 256
        section_idx = in_array // 32
        local = in_array % 32
        group = local // 16
        pos = local % 16
        col_in_section = 1 - group
        row = pos if pos < 8 else (15 - pos) + 9
        return array_idx, section_idx, col_in_section, row

    def _show_context_menu(self, sector_id: int, local, global_pos):
        menu = QMenu(self)
        a_prog = QAction("Program selected region", self)
        a_erase = QAction("Erase selected region", self)
        a_prog.triggered.connect(lambda: self.selection_changed.emit({"action": "program"}))
        a_erase.triggered.connect(lambda: self.selection_changed.emit({"action": "erase"}))
        menu.addAction(a_prog)
        menu.addAction(a_erase)
        self._update_selection(sector_id, local)
        menu.exec(global_pos)

    def _update_selection(self, sector_id: int, local):
        cfg = self.layout_cfg
        lod = self.transform().m11()
        sec_start = sector_start(sector_id)
        level = "sector"
        subidx = None
        size = 0x10000
        start = sec_start
        y_ratio = max(0.0, min(0.999999, local.y() / max(1.0, cfg.tile_h)))
        if lod >= 3.0:
            k = int(y_ratio * 16)
            level = "sub4"
            subidx = k
            size = 0x1000
            start = sec_start + k * 0x1000
        elif lod >= 2.0:
            h = 1 if y_ratio >= 0.5 else 0
            level = "sub32"
            subidx = h
            size = 0x8000
            start = sec_start + h * 0x8000

        self._selection = Selection(level=level, sector_id=sector_id, start=start, size=size, sub32=subidx if level == "sub32" else None, sub4=subidx if level == "sub4" else None)
        self._apply_selection_overlay()
        self.selection_changed.emit({
            "level": level,
            "sector_id": sector_id,
            "start": start,
            "end": start + size - 1,
            "size": size,
            "sub32": self._selection.sub32,
            "sub4": self._selection.sub4,
        })

    def _apply_selection_overlay(self):
        for item in self._items.values():
            item.set_overlay(None, None)
        if not self._selection:
            return
        item = self._items[self._selection.sector_id]
        idx = self._selection.sub32 if self._selection.level == "sub32" else self._selection.sub4
        item.set_overlay(self._selection.level if self._selection.level != "sector" else None, idx)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, SectorItem):
            self.zoom_to_sector(item.sector_id)
        super().mouseDoubleClickEvent(event)


    def focus_sectors(self, sector_ids, target_lod: int = 1):
        ids = list(sector_ids)
        if not ids:
            return
        rect = self._items[ids[0]].sceneBoundingRect()
        for sid in ids[1:]:
            rect = rect.united(self._items[sid].sceneBoundingRect())
        self.fitInView(rect.adjusted(-30, -30, 30, 30), Qt.KeepAspectRatio)
        scale = self.transform().m11()
        if target_lod == 1 and scale >= 2.0:
            self.scale(1.7 / max(scale, 1e-6), 1.7 / max(scale, 1e-6))
        elif target_lod == 1 and scale < 0.45:
            self.scale(0.8 / max(scale, 1e-6), 0.8 / max(scale, 1e-6))
        self.refresh_visible()

    def zoom_to_sector(self, sector_id: int):
        rect = self._items[sector_id].sceneBoundingRect()
        self.fitInView(rect.adjusted(-20, -20, 20, 20), Qt.KeepAspectRatio)
        self.refresh_visible()

    def rotate_quadrant(self, deg: int):
        self.resetTransform()
        self.rotate(deg)
        self.refresh_visible()

    def update_sector_revision(self, sector_id: int):
        self._revisions[sector_id] += 1

    def refresh_visible(self, force: bool = False):
        lod = self._current_lod()
        for sector_id, item in self._items.items():
            if not force and not self._is_item_visible(item):
                continue
            rev = self._revisions[sector_id]
            if lod == 0:
                sbytes = self.model.read(sector_start(sector_id), SECTOR_SIZE)
                erased, ratio = sector_state_summary(sbytes)
                color = QColor(70, 140, 70) if erased else QColor(120 + int(120 * ratio), 170, 70)
                item.set_pixmap(None)
                item.setBrush(QBrush(color))
                continue
            key = (sector_id, self.bitorder, lod, rev)
            cached = self._cache.get(key)
            if cached is not None:
                self._hit += 1
                item.set_pixmap(cached)
            else:
                self._miss += 1
                if key not in self._queued:
                    self._queued.add(key)
                    sbytes = self.model.read(sector_start(sector_id), SECTOR_SIZE)
                    self.thread_pool.start(RenderTask(sector_id, rev, lod, sbytes, self.bitorder, self.signals))
        self._emit_stats()

    def _on_rendered(self, sector_id: int, revision: int, pixmap: QPixmap):
        lod = 1 if pixmap.height() <= 32 else 2
        key = (sector_id, self.bitorder, lod, revision)
        self._cache.put(key, pixmap)
        self._queued.discard(key)
        item = self._items.get(sector_id)
        if item and self._revisions[sector_id] == revision:
            item.set_pixmap(pixmap)
        self._emit_stats()

    def _current_lod(self) -> int:
        scale = self.transform().m11()
        if scale < 0.45:
            return 0
        if scale < 2.0:
            return 1
        return 2

    def _is_item_visible(self, item: QGraphicsItem) -> bool:
        rect = self.mapToScene(self.viewport().rect()).boundingRect()
        return rect.intersects(item.sceneBoundingRect())

    def _emit_stats(self):
        total = self._hit + self._miss
        rate = 0.0 if total == 0 else self._hit / total
        self.stats_changed.emit({"sector_items": len(self._items), "jobs": len(self._queued), "hit_rate": rate})

    @property
    def sector_item_count(self) -> int:
        return len(self._items)
