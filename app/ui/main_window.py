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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOR Flash Visualizer (MT25Q-like)")
        self.resize(1500, 900)
        self.model = MemoryModel()

        self.die = DieView(self.model)
        self.setCentralWidget(self.die)

        self.inspector = InspectorDock(self.model)
        self.program = ProgramDock(self.model)
        self.memmap = MemoryMapDock()

        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.program)
        self.addDockWidget(Qt.RightDockWidgetArea, self.memmap)

        self.program.changed.connect(self.die.refresh_visible)
        self.program.changed.connect(self._refresh_selection)
        self.program.jump_requested.connect(self.jump_to)
        self.die.selection_changed.connect(self.on_selection)

        self._make_menu()

    def _make_menu(self):
        mfile = self.menuBar().addMenu("File")
        mview = self.menuBar().addMenu("View")

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

    def on_selection(self, info: dict):
        if info.get("level") == "sector":
            sid = info["sector_id"]
            self.program.set_selection_sector(sid)
            self.inspector.update_for_sector(sid)

    def _refresh_selection(self):
        self.inspector.update_for_sector(self.program.selection_sector)

    def jump_to(self, addr: int):
        sid = addr >> 16
        self.die.zoom_to_sector(sid)
        self.inspector.update_for_sector(sid)

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
        self.die.refresh_visible()

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", filter="PNG (*.png)")
        if not path:
            return
        pm = self.die.grab()
        pm.save(path)
