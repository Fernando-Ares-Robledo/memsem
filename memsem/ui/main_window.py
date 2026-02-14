from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from memsem.models.flash import FlashBuffer, Region
from memsem.models.layouts import LayoutGrid, Stack16VerticalThenHorizontal, build_folded64_grid
from memsem.models.mt25q import (
    CAPACITY_BYTES,
    PAGE_SIZE,
    SECTOR_SIZE,
    SUB4_SIZE,
    SUB32_SIZE,
    range_for_page,
    range_for_sector,
    range_for_sub4,
    range_for_sub32,
    reference_rows,
)
from memsem.models.paper import BAND_COUNT, SECTOR_SIZE as PAPER_SECTOR_SIZE, build_paper_preset, sector_band_bitmap
from memsem.models.project_io import load_project, save_project
from .die_canvas import DieView, TileInfo


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MemSem Die Visualizer")
        self.resize(1400, 900)
        self.flash = FlashBuffer(CAPACITY_BYTES)
        self.paper = build_paper_preset()
        self.current_layout = build_folded64_grid()
        self.path: list[str] = []

        self.view = DieView(self)
        self.setCentralWidget(self.view)
        self.view.tile_selected.connect(self.on_tile_selected)
        self.view.tile_drilled.connect(self.on_tile_drilled)

        self._build_left_dock()
        self._build_right_dock()
        self._build_menu()

        self.apply_preset("paper")
        self.render()

    def _build_left_dock(self):
        dock = QDockWidget("Controls", self)
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["paper", "mt25q"])
        self.device_combo.currentTextChanged.connect(self.apply_preset)

        self.gran_combo = QComboBox()
        self.gran_combo.addItems([
            "paper_sector",
            "sector64",
            "sub32",
            "sub4",
            "page",
        ])
        self.gran_combo.currentTextChanged.connect(lambda _: self.render())

        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["folded64", "stack16"])
        self.layout_combo.currentTextChanged.connect(lambda _: self.render())

        self.rotation_combo = QComboBox()
        self.rotation_combo.addItems(["0", "90", "180", "270"])
        self.rotation_combo.currentTextChanged.connect(self.apply_rotation)

        self.free_rotate = QSpinBox()
        self.free_rotate.setRange(0, 360)
        self.free_rotate.valueChanged.connect(self.apply_rotation)

        self.band_spin = QSpinBox()
        self.band_spin.setRange(0, BAND_COUNT - 1)
        self.band_spin.valueChanged.connect(self.update_band_preview)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        refs = reference_rows()
        lines = ["Table reference:"]
        for k, rows in refs.items():
            lines.append(k)
            for rid, start, end in rows:
                lines.append(f"  id {rid}: 0x{start:06X}..0x{end:06X}")
        lines.append("A24=0 => sectors 0..255")
        lines.append("A24=1 => sectors 256..511")
        self.info_text.setPlainText("\n".join(lines))

        form = QFormLayout()
        form.addRow("Device", self.device_combo)
        form.addRow("Granularity", self.gran_combo)
        form.addRow("Layout", self.layout_combo)
        form.addRow("Rotate preset", self.rotation_combo)
        form.addRow("Free rotate", self.free_rotate)
        form.addRow("Band index", self.band_spin)
        v.addLayout(form)
        v.addWidget(self.info_text)
        dock.setWidget(wrap)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _build_right_dock(self):
        dock = QDockWidget("Inspector", self)
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        self.selection_label = QLabel("No selection")
        self.breadcrumb_label = QLabel("-")
        self.band_preview = QLabel("Band inspector")
        self.band_preview.setMinimumHeight(240)
        self.band_preview.setScaledContents(True)
        v.addWidget(self.selection_label)
        v.addWidget(self.breadcrumb_label)
        v.addWidget(self.band_preview)
        dock.setWidget(wrap)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _build_menu(self):
        f = self.menuBar().addMenu("File")
        exp = QAction("Export Canvas PNG", self)
        exp.triggered.connect(self.export_canvas)
        save = QAction("Save Project", self)
        save.triggered.connect(self.save_project)
        load = QAction("Load Project", self)
        load.triggered.connect(self.load_project)
        f.addActions([exp, save, load])

    def apply_preset(self, name: str):
        if name == "paper":
            for i, sector in enumerate(self.paper.sectors):
                self.flash.program(Region(i * PAPER_SECTOR_SIZE, PAPER_SECTOR_SIZE), sector, enforce_nor_rule=False)
            self.gran_combo.setCurrentText("paper_sector")
        self.render()

    def current_grid(self, count: int) -> LayoutGrid:
        if self.layout_combo.currentText() == "folded64" and count == 64:
            return build_folded64_grid()
        rows = 16
        cols = max(1, (count + rows - 1) // rows)
        cells = [[None for _ in range(cols)] for _ in range(rows)]
        for i in range(count):
            r, c = Stack16VerticalThenHorizontal.position(i)
            if c < cols:
                cells[r][c] = i
        return LayoutGrid(rows=rows, cols=cols, cells=cells)

    def render(self):
        gran = self.gran_combo.currentText()
        if gran == "paper_sector":
            count, size, range_fn = 16, PAPER_SECTOR_SIZE, lambda i: (i * PAPER_SECTOR_SIZE, (i + 1) * PAPER_SECTOR_SIZE - 1)
        elif gran == "sector64":
            count, size, range_fn = 512, SECTOR_SIZE, range_for_sector
        elif gran == "sub32":
            count, size, range_fn = 1024, SUB32_SIZE, range_for_sub32
        elif gran == "sub4":
            count, size, range_fn = 8192, SUB4_SIZE, range_for_sub4
        else:
            count, size, range_fn = 256, PAGE_SIZE, range_for_page  # manageable zoom page subset
        grid = self.current_grid(min(count, 64 if gran == "page" else count))

        def ratio(info: TileInfo) -> float:
            return self.flash.summary(Region(info.start, info.end - info.start + 1))["ratio_changed"]

        self.view.render_layout(grid.cells, gran, range_fn, ratio)
        self.apply_rotation()

    def on_tile_selected(self, info: TileInfo):
        self.selection_label.setText(f"{info.granularity} #{info.tile_id} 0x{info.start:06X}-0x{info.end:06X}")
        self.statusBar().showMessage(self.selection_label.text())
        self.update_band_preview(info)

    def on_tile_drilled(self, info: TileInfo):
        self.path.append(f"{info.granularity}:{info.tile_id}")
        self.breadcrumb_label.setText(" > ".join(self.path))

    def apply_rotation(self, *_):
        self.view.resetTransform()
        preset = int(self.rotation_combo.currentText())
        self.view.rotate(preset + self.free_rotate.value())

    def update_band_preview(self, info: TileInfo | None = None):
        if info is None and hasattr(self, "_last_info"):
            info = self._last_info
        if info is None:
            return
        self._last_info = info
        if info.granularity != "paper_sector":
            self.band_preview.setText("Band inspector shown for paper sector")
            return
        data = self.flash.read(Region(info.start, PAPER_SECTOR_SIZE))
        bmp = sector_band_bitmap(data, self.band_spin.value())
        rgb = np.zeros((bmp.shape[0], bmp.shape[1], 3), dtype=np.uint8)
        rgb[bmp == 1] = [0x64, 0xB5, 0x5C]
        rgb[bmp == 0] = [0xE6, 0xD3, 0x72]
        h, w, _ = rgb.shape
        img = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        self.band_preview.setPixmap(QPixmap.fromImage(img.copy()).scaled(500, 240, Qt.KeepAspectRatio))

    def export_canvas(self):
        p, _ = QFileDialog.getSaveFileName(self, "Export PNG", "canvas.png", "PNG Files (*.png)")
        if not p:
            return
        pix = self.view.grab()
        pix.save(p)

    def save_project(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save Project", "project.json", "JSON (*.json)")
        if not p:
            return
        payload = {
            "device": self.device_combo.currentText(),
            "granularity": self.gran_combo.currentText(),
            "rotation": int(self.rotation_combo.currentText()),
            "free_rotation": self.free_rotate.value(),
            "memory_changed_ranges": [
                {"start": i, "value": b}
                for i, b in enumerate(self.flash.data)
                if b != 0xFF
            ][:200000],
        }
        save_project(Path(p), payload)

    def load_project(self):
        p, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "JSON (*.json)")
        if not p:
            return
        obj = load_project(Path(p))
        self.device_combo.setCurrentText(obj.get("device", "paper"))
        self.gran_combo.setCurrentText(obj.get("granularity", "paper_sector"))
        self.rotation_combo.setCurrentText(str(obj.get("rotation", 0)))
        self.free_rotate.setValue(obj.get("free_rotation", 0))
