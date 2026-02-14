from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from app.core.mapping import sector_address_range
from app.core.mt25q_model import MT25QModel
from app.core.paper_model import PaperModel
from app.core.patterns import Segment
from app.core.rendering import RenderColors
from .views.mt25q_detail_view import MT25QDetailView
from .views.mt25q_die_view import MT25QDieView
from .views.paper_overview_view import PaperOverviewView
from .views.paper_zoom_view import PaperZoomView
from .widgets.inspector_panel import InspectorPanel
from .widgets.pattern_editor import PatternEditor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flash Memory Pattern Simulator")
        self.resize(1500, 900)

        self.paper_model = PaperModel(bitorder="big")
        self.mt_model = MT25QModel()
        self.colors = RenderColors()
        self.selected_sector = 0

        self._build_topbar()
        self._build_center()
        self._build_docks()
        self._build_menu()
        self.setStatusBar(QStatusBar())

    def _build_topbar(self):
        tb = QToolBar("mode")
        self.addToolBar(tb)
        tb.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Paper", "MT25Q"])
        self.mode_combo.currentTextChanged.connect(self._switch_mode)
        tb.addWidget(self.mode_combo)

        self.bitorder_combo = QComboBox()
        self.bitorder_combo.addItems(["big", "little"])
        self.bitorder_combo.currentTextChanged.connect(self._bitorder_changed)
        tb.addWidget(QLabel("Bit order:"))
        tb.addWidget(self.bitorder_combo)

        jump_btn = QPushButton("Jump to address")
        jump_btn.clicked.connect(self._jump_to_address)
        tb.addWidget(jump_btn)

        erase_sector_btn = QPushButton("Erase selected sector")
        erase_sector_btn.clicked.connect(self._erase_selected_sector)
        tb.addWidget(erase_sector_btn)

        erase_sub4_btn = QPushButton("Erase selected 4KB block")
        erase_sub4_btn.clicked.connect(self._erase_selected_sub4)
        tb.addWidget(erase_sub4_btn)

    def _build_center(self):
        self.center_stack = QStackedWidget()

        paper_container = QWidget()
        pl = QVBoxLayout(paper_container)
        self.paper_overview = PaperOverviewView(self.paper_model, self.colors)
        self.paper_zoom = PaperZoomView(self.paper_model, self.colors)
        self.paper_zoom.selection_changed.connect(self._paper_selection)
        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.paper_overview)
        split.addWidget(self.paper_zoom)
        split.setSizes([320, 560])
        pl.addWidget(split)

        self.mt_die = MT25QDieView(self.mt_model)
        self.mt_die.sector_selected.connect(self._mt_sector_selected)
        self.mt_detail = MT25QDetailView()

        self.center_stack.addWidget(paper_container)
        self.center_stack.addWidget(self.mt_die)
        self.setCentralWidget(self.center_stack)

    def _build_docks(self):
        self.left_dock = QDockWidget("Pattern + Memory Map", self)
        left = QWidget()
        ll = QVBoxLayout(left)
        self.pattern_editor = PatternEditor()
        self.pattern_editor.apply_to_sector.connect(self._program_selected_sector)
        self.pattern_editor.apply_to_sub4.connect(self._program_selected_sub4)
        self.pattern_editor.nor_toggled.connect(self.mt_model.set_nor_enforced)
        ll.addWidget(self.pattern_editor)

        self.mem_map = QTextEdit()
        self.mem_map.setReadOnly(True)
        self.mem_map.setPlainText(self._memory_map_text())
        ll.addWidget(self.mem_map)
        self.left_dock.setWidget(left)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        self.right_dock = QDockWidget("Inspector", self)
        right = QWidget()
        rl = QVBoxLayout(right)
        self.inspector = InspectorPanel()
        rl.addWidget(self.inspector)
        rl.addWidget(self.mt_detail)
        self.right_dock.setWidget(right)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("File")
        save_cfg = QAction("Save config", self)
        load_cfg = QAction("Load config", self)
        exp_png = QAction("Export PNG", self)
        save_cfg.triggered.connect(self._save_config)
        load_cfg.triggered.connect(self._load_config)
        exp_png.triggered.connect(self._export_png)
        file_menu.addAction(save_cfg)
        file_menu.addAction(load_cfg)
        file_menu.addAction(exp_png)

    def _switch_mode(self, mode: str):
        self.center_stack.setCurrentIndex(0 if mode == "Paper" else 1)

    def _bitorder_changed(self, bitorder: str):
        self.paper_model.bitorder = bitorder
        self.paper_overview.refresh()
        self.paper_zoom.refresh()

    def _paper_selection(self, payload: dict):
        text = (
            f"Sector: {payload['sector']}\nBand: {payload['band']}\n"
            f"Cell: (r={payload['row']}, c={payload['col']})\n"
            f"Bit value: {payload['bit']}\n"
            f"Word index: {payload['row'] * 256 + payload['col']}\n"
            f"Word bytes: {payload['word_hex']}\nASCII: {payload['ascii']}\n\n"
            f"16x16 bit grid:\n{payload['bit_grid']}"
        )
        self.inspector.set_text(text)

    def _memory_map_text(self) -> str:
        return (
            "Sector map formula:\n"
            "start = sector_id * 0x10000\nend = start + 0xFFFF\n"
            "Examples: sector 0 0x000000-0x00FFFF; sector 255 0xFF0000-0xFFFFFF; "
            "sector 256 0x01000000-0x0100FFFF; sector 511 0x01FF0000-0x01FFFFFF\n\n"
            "4KB subsector formula:\nstart = sub4_id * 0x1000\nend = start + 0xFFF\n"
            "Examples: sub4 0 0x000000-0x000FFF; sub4 8191 0x01FFF000-0x01FFFFFF\n\n"
            "32KB subsector formula:\nstart = sub32_id * 0x8000\nend = start + 0x7FFF\n"
            "Examples: sub32 0 0x000000-0x007FFF; sub32 1023 0x01FF8000-0x01FFFFFF\n\n"
            "Page formula:\nstart = page_id * 0x100\nend = start + 0xFF\n"
            "Extended addressing concept:\nA24=0: sectors 0..255; A24=1: sectors 256..511"
        )


    def _mt_sector_selected(self, sector_id: int):
        self.selected_sector = sector_id
        self.mt_detail.set_sector(sector_id)
        start, end = sector_address_range(sector_id)
        self.inspector.set_text(
            f"sector_id={sector_id}\n"
            f"bank={sector_id // 256}\n"
            f"grid(row,col)=({sector_id % 16},{(sector_id % 256) // 16})\n"
            f"range=0x{start:08X}-0x{end:08X}\n"
            "32KB offsets: 0x0000,0x8000\n"
            "4KB offsets: 0x0000..0xF000 step 0x1000\n"
            "pages: 0x0000..0xFF00 step 0x100"
        )

    def _jump_to_address(self):
        text, ok = QInputDialog.getText(self, "Jump", "Address (hex, e.g. 0x1234):")
        if not ok or not text:
            return
        addr = int(text, 16)
        info = self.mt_model.jump_to_address(addr)
        self.selected_sector = info["sector_id"]
        self.mt_detail.set_sector(self.selected_sector)
        self.inspector.set_text(json.dumps({k: str(v) for k, v in info.items()}, indent=2))

    def _program_selected_sector(self, segments: list[Segment]):
        if self.mode_combo.currentText() == "Paper":
            self.paper_model.set_segment_config(self.paper_zoom.sector.value(), segments)
            self.paper_overview.refresh()
            self.paper_zoom.refresh()
            return
        start, _ = sector_address_range(self.selected_sector)
        self.mt_model.program(start, 0x10000, segments)
        self.mt_die.refresh()

    def _erase_selected_sector(self):
        if self.mode_combo.currentText() != "MT25Q":
            return
        start, _ = sector_address_range(self.selected_sector)
        self.mt_model.erase(start, 0x10000)
        self.mt_die.refresh()

    def _program_selected_sub4(self, segments: list[Segment]):
        if self.mode_combo.currentText() != "MT25Q":
            return
        start, _ = sector_address_range(self.selected_sector)
        self.mt_model.program(start, 0x1000, segments)
        self.mt_die.refresh()

    def _erase_selected_sub4(self):
        if self.mode_combo.currentText() != "MT25Q":
            return
        start, _ = sector_address_range(self.selected_sector)
        self.mt_model.erase(start, 0x1000)
        self.mt_die.refresh()

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", "view.png", "PNG (*.png)")
        if not path:
            return
        if self.mode_combo.currentText() == "Paper":
            img = self.paper_zoom.view.grab()
        else:
            img = self.mt_die.view.grab()
        img.save(path)

    def _save_config(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Config", "config.json", "JSON (*.json)")
        if not path:
            return
        cfg = {
            "mode": self.mode_combo.currentText(),
            "bitorder": self.bitorder_combo.currentText(),
            "paper": {
                str(k): [s.__dict__ for s in v] for k, v in self.paper_model.segments.items()
            },
            "mt25q_dump_full": None,
            "visualization": {"one": self.colors.one, "zero": self.colors.zero},
        }
        mem = self.mt_model.memory.tobytes()
        cfg["mt25q_dump_full"] = gzip.compress(mem).hex()
        Path(path).write_text(json.dumps(cfg, indent=2))

    def _load_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "JSON (*.json)")
        if not path:
            return
        cfg = json.loads(Path(path).read_text())
        self.mode_combo.setCurrentText(cfg.get("mode", "Paper"))
        self.bitorder_combo.setCurrentText(cfg.get("bitorder", "big"))
        paper = cfg.get("paper", {})
        for k, segs in paper.items():
            self.paper_model.segments[int(k)] = [Segment(**s) for s in segs]
        dump_hex = cfg.get("mt25q_dump_full")
        if dump_hex:
            raw = gzip.decompress(bytes.fromhex(dump_hex))
            self.mt_model.memory = np.frombuffer(raw, dtype=np.uint8).copy()
        self.paper_overview.refresh()
        self.paper_zoom.refresh()
        self.mt_die.refresh()
