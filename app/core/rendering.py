from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    from PySide6.QtCore import QObject, QRunnable, Signal
    from PySide6.QtGui import QImage, QColor
except Exception:  # allows headless test environment without Qt libs
    QObject = object
    QRunnable = object

    class _DummySignal:
        def emit(self, *args, **kwargs):
            pass

    def Signal(*args, **kwargs):  # type: ignore
        return _DummySignal()

    class QColor:  # type: ignore
        def __init__(self, *args):
            self.args = args

    QImage = None

from .paper_model import PaperModel


@dataclass
class RenderColors:
    one: tuple[int, int, int] = (89, 170, 115)
    zero: tuple[int, int, int] = (220, 210, 102)


class RenderSignals(QObject):
    finished = Signal(int, object)


class PaperSectorRenderTask(QRunnable):
    def __init__(self, model: PaperModel, sector_id: int, colors: RenderColors, cell_size: int = 1):
        super().__init__()
        self.model = model
        self.sector_id = sector_id
        self.colors = colors
        self.cell_size = cell_size
        self.signals = RenderSignals()

    def run(self) -> None:
        img = render_sector_thumbnail(self.model, self.sector_id, self.colors, self.cell_size)
        self.signals.finished.emit(self.sector_id, img)


def _bits_to_rgb(bits: np.ndarray, colors: RenderColors) -> np.ndarray:
    one = np.array(colors.one, dtype=np.uint8)
    zero = np.array(colors.zero, dtype=np.uint8)
    return np.where(bits[..., None] == 1, one, zero)


def render_band_tile_rgb(tile_bits: np.ndarray, colors: RenderColors, cell_size: int = 3) -> np.ndarray:
    rgb = _bits_to_rgb(tile_bits, colors)
    if cell_size > 1:
        rgb = np.repeat(np.repeat(rgb, cell_size, axis=0), cell_size, axis=1)
    return rgb


def render_band_tile_image(tile_bits: np.ndarray, colors: RenderColors, cell_size: int = 3):
    rgb = render_band_tile_rgb(tile_bits, colors, cell_size)
    if QImage is None:
        return rgb
    h, w, _ = rgb.shape
    qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return qimg.copy()


def render_sector_thumbnail_rgb(model: PaperModel, sector_id: int, colors: RenderColors, cell_size: int = 1) -> np.ndarray:
    rows = []
    for b in range(256):
        rows.append(model.band_tile(sector_id, b))
    stack = np.vstack(rows)
    return render_band_tile_rgb(stack, colors, cell_size)


def render_sector_thumbnail(model: PaperModel, sector_id: int, colors: RenderColors, cell_size: int = 1):
    rgb = render_sector_thumbnail_rgb(model, sector_id, colors, cell_size)
    if QImage is None:
        return rgb
    h, w, _ = rgb.shape
    qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return qimg.copy()


def color_for_density(density: float) -> QColor:
    if density <= 0.0:
        return QColor(230, 230, 230)
    val = int(70 + min(1.0, density) * 150)
    return QColor(120, 80, val)
