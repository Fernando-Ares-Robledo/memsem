from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow

from core.model import MemoryModel
from core.utils import load_json, save_json
from .die_view import DieView
from .inspector_dock import InspectorDock
from .memory_map_dock import MemoryMapDock
from .program_dock import ProgramDock
from .row_strip_dock import RowStripDock


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOR Flash Visualizer (MT25Q-like)")
        self.resize(1600, 920)
        self.model = MemoryModel()

        self.die = DieView(self.model)
        self.setCentralWidget(self.die)

        self.inspector = InspectorDock(self.model)
        self.program = ProgramDock(self.model)
        self.memmap = MemoryMapDock()
        self.row_strip = RowStripDock(self.model)

        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.program)
        self.addDockWidget(Qt.RightDockWidgetArea, self.memmap)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.row_strip)

        self.program.changed.connect(self.on_memory_changed)
        self.program.jump_requested.connect(self.jump_to)
        self.die.selection_changed.connect(self.on_selection)
        self.die.row_picked.connect(self.row_strip.show_row)
        self.row_strip.sector_activated.connect(self.jump_to_sector)
        self.die.stats_changed.connect(self.on_stats)

        self._last_selection = {"level": "sector", "sector_id": 0, "start": 0, "size": 0x10000, "end": 0xFFFF}
        self._make_menu()
        self.statusBar().showMessage("Ready")

    def _make_menu(self):
        mfile = self.menuBar().addMenu("File")
        mview = self.menuBar().addMenu("View")
        mtools = self.menuBar().addMenu("Tools")

        save = QAction("Save Project", self)
        load = QAction("Load Project", self)
        export = QAction("Export PNG", self)
        save.triggered.connect(self.save_project)
        load.triggered.connect(self.load_project)
        export.triggered.connect(self.export_png)
        mfile.addActions([save, load, export])

        for deg in [0, 90, 180, 270]:
            a = QAction(f"Rotate {deg}", self)
            a.triggered.connect(lambda checked=False, d=deg: self.die.rotate_quadrant(d))
            mview.addAction(a)

        pick_row = QAction("Pick row", self)
        pick_row.triggered.connect(lambda: self.die.set_row_pick_mode(True))
        mtools.addAction(pick_row)

    def on_selection(self, info: dict):
        if info.get("action") == "program":
            self.program._program()
            return
        if info.get("action") == "erase":
            self.program._erase()
            return

        if "sector_id" in info:
            self._last_selection = info
            self.program.set_selected_region(info)
            self.inspector.update_for_selection(info)

    def on_memory_changed(self, region: dict):
        start = region["start"]
        end = start + region["size"] - 1
        first = start >> 16
        last = end >> 16
        for sid in range(first, last + 1):
            self.die.update_sector_revision(sid)
        self.die.refresh_visible()
        self.inspector.update_for_selection(self._last_selection)

    def on_stats(self, s: dict):
        self.statusBar().showMessage(
            f"tiles={s['sector_items']} jobs={s['jobs']} cache_hit={s['hit_rate']:.1%}"
        )

    def jump_to(self, addr: int):
        self.jump_to_sector(addr >> 16)

    def jump_to_sector(self, sid: int):
        self.die.zoom_to_sector(sid)
        info = {"level": "sector", "sector_id": sid, "start": sid << 16, "size": 0x10000, "end": (sid << 16) + 0xFFFF}
        self.program.set_selected_region(info)
        self.inspector.update_for_selection(info)

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", filter="Project (*.json)")
        if not path:
            return
        bpath = path + ".bin"
        with open(bpath, "wb") as f:
            f.write(self.model.mem)
        save_json(path, {"bin": bpath, "visual": {"bitorder": self.die.bitorder, "show_ecc": self.die.show_ecc}})

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Project", filter="Project (*.json)")
        if not path:
            return
        meta = load_json(path)
        with open(meta["bin"], "rb") as f:
            self.model.mem[:] = f.read()
        self.die.bitorder = meta.get("visual", {}).get("bitorder", "msb")
        self.die.show_ecc = meta.get("visual", {}).get("show_ecc", True)
        for sid in range(512):
            self.die.update_sector_revision(sid)
        self.die.refresh_visible(force=True)

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", filter="PNG (*.png)")
        if not path:
            return
        self.die.grab().save(path)
