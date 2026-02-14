from __future__ import annotations

import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import QDockWidget, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from core.addressing import SECTOR_SIZE, sector_start
from core.layout import column_sector_ids_8x2, row_strip_order
from core.render import sector_detailed_image


class RowStripDock(QDockWidget):
    sector_activated = Signal(int)

    def __init__(self, model, parent=None):
        super().__init__("Row/Column Strip View", parent)
        self.model = model
        body = QWidget()
        lay = QVBoxLayout(body)
        self.label = QLabel("Pick a row/column from die view")
        self.listw = QListWidget()
        self.listw.setViewMode(QListWidget.IconMode)
        self.listw.setResizeMode(QListWidget.Adjust)
        self.listw.setMovement(QListWidget.Static)
        self.listw.setIconSize(QPixmap(180, 80).size())
        self.listw.itemClicked.connect(self._on_item)
        lay.addWidget(self.label)
        lay.addWidget(self.listw)
        self.setWidget(body)

    def _show_sector_list(self, label: str, left: list[int], right: list[int]):
        self.label.setText(label)
        self.listw.clear()
        for sec in left:
            self.listw.addItem(self._item_for_sector(sec))
        sep = QListWidgetItem("| Sector |")
        sep.setFlags(Qt.NoItemFlags)
        self.listw.addItem(sep)
        for sec in right:
            self.listw.addItem(self._item_for_sector(sec))

    def show_row(self, array_idx: int, row: int):
        left, right = row_strip_order(array_idx, row)
        self._show_sector_list(f"Array {array_idx}, row {row}: 0..7 | Sector | 15..8", left, right)

    def show_column(self, array_idx: int, section_idx: int, col_in_section: int):
        ids = column_sector_ids_8x2(array_idx, section_idx, col_in_section)
        left = ids[:8]
        right = ids[8:]  # already 15..8 order by construction
        self._show_sector_list(
            f"Array {array_idx}, section {section_idx}, col {col_in_section}: 0..7 | Sector | 15..8",
            left,
            right,
        )

    def _item_for_sector(self, sector_id: int) -> QListWidgetItem:
        sbytes = self.model.read(sector_start(sector_id), SECTOR_SIZE)
        arr = sector_detailed_image(sbytes, height=220, with_ecc=False, orientation="vertical")
        arr = np.ascontiguousarray(arr, dtype=np.uint8)
        h, w, _ = arr.shape
        img = QImage(arr.data, w, h, 3 * w, QImage.Format_RGB888)
        pm = QPixmap.fromImage(img.copy()).scaled(95, 200, Qt.KeepAspectRatio, Qt.FastTransformation)
        it = QListWidgetItem(f"S{sector_id}")
        it.setData(Qt.UserRole, sector_id)
        it.setIcon(QIcon(pm))
        return it

    def _on_item(self, item: QListWidgetItem):
        sid = item.data(Qt.UserRole)
        if sid is not None:
            self.sector_activated.emit(int(sid))
