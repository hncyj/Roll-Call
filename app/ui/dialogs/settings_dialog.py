from __future__ import annotations
import os

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

from app.config import get_app_dir, DEFAULT_DATA_FILENAME


class SettingsDialog(QDialog):
    def __init__(self, current_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("数据文件路径："))
        hint = QLabel("选择新文件：复制当前数据并记住新路径。\n选择已有文件：打开其中的数据，不覆盖文件。\n重启后继续使用此路径；外部存储设备需保持连接。")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        path_row = QHBoxLayout()
        self._edit = QLineEdit(current_path)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse)
        default_btn = QPushButton("恢复默认")
        default_btn.clicked.connect(self._restore_default)
        path_row.addWidget(self._edit)
        path_row.addWidget(browse_btn)
        path_row.addWidget(default_btn)
        layout.addLayout(path_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "选择数据文件位置", self._edit.text(), "JSON Files (*.json)",
            options=QFileDialog.DontConfirmOverwrite,
        )
        if path:
            self._edit.setText(path)

    def _restore_default(self):
        self._edit.setText(os.path.join(get_app_dir(), DEFAULT_DATA_FILENAME))

    def selected_path(self) -> str:
        return self._edit.text().strip()
