import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PySide6.QtWidgets", reason="Qt runtime libs not available", exc_type=ImportError)

from core.model import MemoryModel
from ui.die_view import DieView


@pytest.mark.skipif(not hasattr(QtWidgets, "QApplication"), reason="QApplication unavailable")
def test_die_scene_has_exactly_512_sector_items():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    view = DieView(MemoryModel())
    assert view.sector_item_count == 512
    app.quit()
