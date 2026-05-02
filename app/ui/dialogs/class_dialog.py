from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout,
)


class CreateClassDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建班级")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("班级名称："))
        self._edit = QLineEdit()
        layout.addWidget(self._edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def class_name(self) -> str:
        return self._edit.text().strip()

    def accept(self):
        if self.class_name():
            super().accept()


class RenameClassDialog(QDialog):
    def __init__(self, old_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("重命名班级")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("新班级名称："))
        self._edit = QLineEdit(old_name)
        self._edit.selectAll()
        layout.addWidget(self._edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def class_name(self) -> str:
        return self._edit.text().strip()

    def accept(self):
        if self.class_name():
            super().accept()


class DeleteClassDialog(QDialog):
    def __init__(self, class_name: str, parent=None):
        super().__init__(parent)
        self._expected = class_name
        self.setWindowTitle("删除班级")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'此操作不可恢复。\n请输入班级名称 "{class_name}" 确认删除：'))
        self._edit = QLineEdit()
        layout.addWidget(self._edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        if self._edit.text().strip() == self._expected:
            super().accept()
