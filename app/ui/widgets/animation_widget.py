from __future__ import annotations
import random
from typing import List

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class AnimationWidget(QWidget):
    animation_finished = pyqtSignal(object)  # emits Student

    _INTERVALS = [50, 50, 50, 50, 80, 80, 120, 150, 200, 280, 350, 400]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._label = QLabel("--")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("font-size: 36px; font-weight: bold; padding: 20px;")
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._names: List[str] = []
        self._target = None
        self._step = 0

    def start(self, names: List[str], target) -> None:
        self._names = names
        self._target = target
        self._step = 0
        self._timer.start(self._INTERVALS[0])

    def _tick(self) -> None:
        if self._target is None:
            return
        self._step += 1
        if self._step >= len(self._INTERVALS):
            self._timer.stop()
            self._label.setText(self._target.name)
            self.animation_finished.emit(self._target)
            return
        self._label.setText(random.choice(self._names))
        self._timer.start(self._INTERVALS[self._step])

    def set_text(self, text: str) -> None:
        self._label.setText(text)

    def cancel(self) -> None:
        self._timer.stop()
        self._target = None
        self._names = []
        self._label.setText("--")

    @property
    def is_animating(self) -> bool:
        return self._timer.isActive()
