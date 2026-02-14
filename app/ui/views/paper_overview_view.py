from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.core.paper_model import PaperModel
from app.core.rendering import RenderColors, render_sector_thumbnail
from .common import ZoomableGraphicsView


class _BankPane(QWidget):
    def __init__(self, sectors: list[int], model: PaperModel, colors: RenderColors, parent=None):
        super().__init__(parent)
        self.sectors = sectors
        self.model = model
        self.colors = colors

        layout = QVBoxLayout(self)
        self.view = ZoomableGraphicsView()
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        fit = QPushButton("Fit")
        fit.clicked.connect(self.view.fit_scene)
        layout.addWidget(fit)
        layout.addWidget(self.view)

    def rebuild(self):
        self.scene.clear()
        y = 0
        for sid in self.sectors:
            img = render_sector_thumbnail(self.model, sid, self.colors, 1)
            pix = QPixmap.fromImage(img)
            item = QGraphicsPixmapItem(pix)
            item.setPos(0, y)
            self.scene.addItem(item)
            y += pix.height() + 6


class PaperOverviewView(QWidget):
    def __init__(self, model: PaperModel, colors: RenderColors, parent=None):
        super().__init__(parent)
        self.model = model
        bank1, bank2 = self.model.bank_layout()

        split = QSplitter(Qt.Orientation.Horizontal)
        self.left = _BankPane(bank1, self.model, colors)
        self.right = _BankPane(bank2, self.model, colors)
        split.addWidget(self.left)
        split.addWidget(self.right)

        layout = QHBoxLayout(self)
        layout.addWidget(split)
        self.refresh()

    def refresh(self):
        self.left.rebuild()
        self.right.rebuild()
