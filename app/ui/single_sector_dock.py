from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDockWidget, QLabel, QVBoxLayout, QWidget

from core.addressing import SECTOR_SIZE, sector_start
from core.render import sector_detailed_image


class SingleSectorDock(QDockWidget):
    def __init__(self, model, parent=None):
        super().__init__("Single Sector View", parent)
        self.model = model
        body = QWidget()
        lay = QVBoxLayout(body)
        self.title = QLabel("Select a sector")
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.title)
        lay.addWidget(self.preview)
        self.setWidget(body)

    def show_sector(self, sector_id: int, bitorder: str = "msb"):
        self.title.setText(f"Sector {sector_id}")
        sbytes = self.model.read(sector_start(sector_id), SECTOR_SIZE)
        arr = sector_detailed_image(sbytes, height=320, with_ecc=True, bitorder=bitorder, orientation="vertical")
        h, w, _ = arr.shape
        img = QImage(arr.data, w, h, 3 * w, QImage.Format_RGB888)
        pm = QPixmap.fromImage(img.copy()).scaled(220, 620, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.preview.setPixmap(pm)
