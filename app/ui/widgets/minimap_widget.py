from __future__ import annotations

from PySide6.QtWidgets import QLabel


class MinimapWidget(QLabel):
    """Optional placeholder minimap widget."""

    def __init__(self, parent=None):
        super().__init__("Minimap (optional)", parent)
