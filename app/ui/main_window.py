from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QToolBar

from core.model import MemoryModel
from core.preset import apply_paper_like_preset, validate_paper_like_hashes
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
        self.program.sector_selected.connect(self.jump_to_sector)
        self.die.selection_changed.connect(self.on_selection)
        self.die.row_picked.connect(self.row_strip.show_row)
        self.die.column_picked.connect(self.row_strip.show_column)
        self.row_strip.sector_activated.connect(self.jump_to_sector)
        self.die.stats_changed.connect(self.on_stats)

        self._last_selection = {"level": "sector", "sector_id": 0, "start": 0, "size": 0x10000, "end": 0xFFFF}
        self._make_menu_toolbar()
        self.statusBar().showMessage("Ready")

    def _make_menu_toolbar(self):
        mfile = self.menuBar().addMenu("File")
        mview = self.menuBar().addMenu("View")
        mtools = self.menuBar().addMenu("Tools")

        save = QAction("Save Project", self)
        load = QAction("Load Project", self)
        export = QAction("Export PNG", self)
        preset = QAction("Load Paper-like Preset", self)

        save.triggered.connect(self.save_project)
        load.triggered.connect(self.load_project)
        export.triggered.connect(self.export_png)
        preset.triggered.connect(self.load_paper_like_preset)
        mfile.addActions([save, load, export, preset])

        toolbar = QToolBar("Main", self)
        toolbar.addAction(QAction("Preset", self, triggered=self.load_paper_like_preset))
        self.addToolBar(toolbar)

        for deg in [0, 90, 180, 270]:
            a = QAction(f"Rotate {deg}", self)
            a.triggered.connect(lambda checked=False, d=deg: self.die.rotate_quadrant(d))
            mview.addAction(a)

        pick_row = QAction("Pick row", self)
        pick_row.triggered.connect(lambda: self.die.set_row_pick_mode(True))
        mtools.addAction(pick_row)

        pick_col = QAction("Pick column", self)
        pick_col.triggered.connect(lambda: self.die.set_column_pick_mode(True))
        mtools.addAction(pick_col)

    def load_paper_like_preset(self):
        apply_paper_like_preset(self.model)
        for sid in range(16):
            self.die.update_sector_revision(sid)
        self.die.refresh_visible()
        self.die.focus_sectors(range(16), target_lod=1)

        hashes, results = validate_paper_like_hashes(self.model, bitorder=self.die.bitorder)
        self.program.append_log("[Preset] Applied sectors 0..15")
        self.program.append_log(f"hash(s0)={hashes[0]} hash(s12)={hashes[12]}")
        self.program.append_log(f"hash(s7)={hashes[7]} hash(s10)={hashes[10]}")
        self.program.append_log(f"hash(s5)={hashes[5]} hash(s8)={hashes[8]}")
        self.program.append_log(f"hash(s6)={hashes[6]} hash(s11)={hashes[11]}")
        mismatch = [r for r in results if not r.match]
        if mismatch:
            self.program.append_log("[WARNING] Visual validation mismatch found")
            self.statusBar().showMessage("Preset loaded with validation mismatch", 6000)
        else:
            self.program.append_log("[OK] Visual validation matched for all required pairs")
            self.statusBar().showMessage("Preset loaded and validated", 6000)

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
        self.statusBar().showMessage(f"tiles={s['sector_items']} jobs={s['jobs']} cache_hit={s['hit_rate']:.1%}")

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
