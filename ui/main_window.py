from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.addressing import sector_range, sub4_range, sub32_range
from core.constants import SECTOR_SIZE_64K, SUBSECTOR_SIZE_32K, SUBSECTOR_SIZE_4K
from core.model import FlashModel, Selection
from core.patterns import PatternSegment, build_pattern
from ui.die_view import DieView
from ui.inspector import InspectorWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = FlashModel()
        self.setWindowTitle("MT25Q NOR Flash Visualizer")
        self.resize(1500, 900)

        self.die = DieView(self.model)
        self.setCentralWidget(self.die)
        self.inspector = InspectorWidget(self.model)
        self.selection: Selection | None = None

        self._build_left_dock()
        self._build_right_dock()
        self._build_menu()

        self.die.selection_changed.connect(self.on_selection)

    def _build_left_dock(self):
        dock = QDockWidget("Controls", self)
        container = QWidget()
        v = QVBoxLayout(container)

        self.sel_label = QLabel("No selection")
        v.addWidget(self.sel_label)

        mmap = QLabel("""Memory Map (Table-2 style):
64KB sector: start=sector_id*0x10000, end=start+0xFFFF
32KB: start=sub32_id*0x8000, end=start+0x7FFF
4KB: start=sub4_id*0x1000, end=start+0xFFF
Page: start=page_id*0x100, end=start+0xFF
A24=0 => sectors 0..255, A24=1 => sectors 256..511""")
        mmap.setWordWrap(True)
        v.addWidget(mmap)

        self.region_kind = QComboBox()
        self.region_kind.addItems(["sector64", "sub32", "sub4", "range"])
        self.region_id = QSpinBox()
        self.region_id.setRange(0, 8191)
        self.range_start = QLineEdit("0x000000")
        self.range_size = QLineEdit("0x1000")
        self.enforce_nor = QCheckBox("Enforce NOR 1->0 only")
        self.enforce_nor.setChecked(True)

        form = QFormLayout()
        form.addRow("Region", self.region_kind)
        form.addRow("ID", self.region_id)
        form.addRow("Range start", self.range_start)
        form.addRow("Range size", self.range_size)
        form.addRow(self.enforce_nor)

        self.seg1_type = QComboBox(); self.seg1_type.addItems(["text", "hex", "fill"])
        self.seg1_val = QLineEdit("AA")
        self.seg2_type = QComboBox(); self.seg2_type.addItems(["text", "hex", "fill"])
        self.seg2_val = QLineEdit("")
        form.addRow("Seg1", self.seg1_type)
        form.addRow("Seg1 value", self.seg1_val)
        form.addRow("Seg2", self.seg2_type)
        form.addRow("Seg2 value", self.seg2_val)

        v.addLayout(form)

        row = QHBoxLayout()
        program_btn = QPushButton("Program")
        erase_btn = QPushButton("Erase")
        row.addWidget(program_btn)
        row.addWidget(erase_btn)
        v.addLayout(row)

        jump_btn = QPushButton("Jump to address")
        self.jump_addr = QLineEdit("0x000000")
        v.addWidget(self.jump_addr)
        v.addWidget(jump_btn)

        rotate_row = QHBoxLayout()
        for deg in [0, 90, 180, 270]:
            b = QPushButton(f"{deg}°")
            b.clicked.connect(lambda _, d=deg: self.die.set_rotation(d))
            rotate_row.addWidget(b)
        v.addLayout(rotate_row)

        program_btn.clicked.connect(self.on_program)
        erase_btn.clicked.connect(self.on_erase)
        jump_btn.clicked.connect(self.on_jump)

        dock.setWidget(container)
        self.addDockWidget(0x1, dock)

    def _build_right_dock(self):
        dock = QDockWidget("Inspector", self)
        dock.setWidget(self.inspector)
        self.addDockWidget(0x2, dock)

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("File")
        save_act = QAction("Save Project", self)
        load_act = QAction("Load Project", self)
        export_die = QAction("Export Die PNG", self)
        export_inspector = QAction("Export Inspector PNG", self)
        save_act.triggered.connect(self.save_project)
        load_act.triggered.connect(self.load_project)
        export_die.triggered.connect(self.export_die)
        export_inspector.triggered.connect(self.export_inspector)
        file_menu.addActions([save_act, load_act, export_die, export_inspector])

    def on_selection(self, sel: Selection):
        self.selection = sel
        self.sel_label.setText(f"{sel.level} 0x{sel.start:06X}-0x{sel.end:06X}")
        self.inspector.set_selection(sel)
        self.statusBar().showMessage(f"Selection {sel.level} | zoom={self.die.scale_factor:.2f} | rot={self.die.rotation_deg}")

    def _resolve_region(self) -> tuple[int, int]:
        kind = self.region_kind.currentText()
        idx = self.region_id.value()
        if kind == "sector64":
            return sector_range(idx)[0], SECTOR_SIZE_64K
        if kind == "sub32":
            return sub32_range(idx)[0], SUBSECTOR_SIZE_32K
        if kind == "sub4":
            return sub4_range(idx)[0], SUBSECTOR_SIZE_4K
        start = int(self.range_start.text(), 16)
        size = int(self.range_size.text(), 16)
        return start, size

    def on_program(self):
        start, size = self._resolve_region()
        segments = [PatternSegment(self.seg1_type.currentText(), self.seg1_val.text())]
        if self.seg2_val.text().strip():
            segments.append(PatternSegment(self.seg2_type.currentText(), self.seg2_val.text()))
        payload = build_pattern(size, segments)
        self.model.program(start, payload, self.enforce_nor.isChecked())
        self.die.rebuild_scene()
        self.on_selection(Selection(start, size, self.region_kind.currentText()))

    def on_erase(self):
        start, size = self._resolve_region()
        self.model.erase(start, size)
        self.die.rebuild_scene()
        self.on_selection(Selection(start, size, self.region_kind.currentText()))

    def on_jump(self):
        try:
            addr = int(self.jump_addr.text(), 16)
            sid = addr // SECTOR_SIZE_64K
            self.on_selection(Selection(sid * SECTOR_SIZE_64K, SECTOR_SIZE_64K, "sector64"))
        except Exception as exc:
            QMessageBox.warning(self, "Invalid address", str(exc))

    def save_project(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save project", filter="Project (*.json)")
        if not fn:
            return
        path = Path(fn)
        bin_path = path.with_suffix(".bin")
        ui_settings = {
            "word_bits": self.inspector.word_bits.value(),
            "bitorder": "msb" if self.inspector.bitorder.isChecked() else "lsb",
        }
        self.model.save_project(path, bin_path, ui_settings)

    def load_project(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Load project", filter="Project (*.json)")
        if not fn:
            return
        settings = self.model.load_project(Path(fn))
        self.inspector.word_bits.setValue(settings.get("word_bits", 256))
        self.inspector.bitorder.setChecked(settings.get("bitorder", "msb") == "msb")
        self.die.rebuild_scene()

    def export_die(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Export Die", filter="PNG (*.png)")
        if not fn:
            return
        pixmap = self.die.grab()
        pixmap.save(fn)

    def export_inspector(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Export Inspector", filter="PNG (*.png)")
        if not fn:
            return
        self.inspector.grab().save(fn)
