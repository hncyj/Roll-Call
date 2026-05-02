from __future__ import annotations
from typing import List

from PyQt5.QtWidgets import QGroupBox, QLabel, QListWidget, QVBoxLayout, QWidget

from app.data.models import Student


class StatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._called_label = QLabel("已点名（0）")
        self._called_list = QListWidget()
        called_group = QGroupBox()
        called_layout = QVBoxLayout(called_group)
        called_layout.addWidget(self._called_label)
        called_layout.addWidget(self._called_list)

        self._uncalled_label = QLabel("未点名（0）")
        self._uncalled_list = QListWidget()
        uncalled_group = QGroupBox()
        uncalled_layout = QVBoxLayout(uncalled_group)
        uncalled_layout.addWidget(self._uncalled_label)
        uncalled_layout.addWidget(self._uncalled_list)

        layout.addWidget(called_group)
        layout.addWidget(uncalled_group)

    def refresh(self, called: List[Student], uncalled: List[Student]) -> None:
        self._called_label.setText(f"已点名（{len(called)}）")
        self._called_list.clear()
        for s in called:
            self._called_list.addItem(f"{s.id}  {s.name}")

        self._uncalled_label.setText(f"未点名（{len(uncalled)}）")
        self._uncalled_list.clear()
        for s in uncalled:
            self._uncalled_list.addItem(f"{s.id}  {s.name}")
