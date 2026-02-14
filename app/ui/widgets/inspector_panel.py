from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class InspectorPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.title = QLabel("Inspector")
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        layout.addWidget(self.title)
        layout.addWidget(self.details)

    def set_text(self, text: str) -> None:
        self.details.setPlainText(text)
