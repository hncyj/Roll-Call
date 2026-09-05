from __future__ import annotations
import uuid
import os

from PyQt5.QtWidgets import (
    QAction, QComboBox, QMainWindow, QMessageBox,
    QPushButton, QTabWidget, QToolBar, QWidget,
)

from app.data.models import ClassData
from app.data.repository import Repository
from app.ui.dialogs.class_dialog import (
    CreateClassDialog, DeleteClassDialog, RenameClassDialog,
)
from app.ui.dialogs.settings_dialog import SettingsDialog
from app.ui.tab_records import RecordsTab
from app.ui.tab_roll_call import RollCallTab
from app.ui.tab_students import StudentsTab


class MainWindow(QMainWindow):
    def __init__(self, repo=None):
        super().__init__()
        self.setWindowTitle("随机点名系统")
        self.setMinimumSize(1000, 680)

        self._repo = repo if repo is not None else Repository()
        self._data = self._repo.load()

        self._init_toolbar()
        self._init_tabs()
        self._refresh_class_combo()

    def _init_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._class_combo = QComboBox()
        self._class_combo.setMinimumWidth(160)
        self._class_combo.currentIndexChanged.connect(self._on_class_changed)
        toolbar.addWidget(self._class_combo)
        toolbar.addSeparator()

        add_btn = QPushButton("＋ 新建班级")
        add_btn.clicked.connect(self._create_class)
        rename_btn = QPushButton("✎ 重命名")
        rename_btn.clicked.connect(self._rename_class)
        del_btn = QPushButton("🗑 删除班级")
        del_btn.clicked.connect(self._delete_class)
        for btn in (add_btn, rename_btn, del_btn):
            toolbar.addWidget(btn)

        spacer = QWidget()
        spacer.setMinimumWidth(20)
        toolbar.addWidget(spacer)

        settings_action = QAction("⚙ 设置", self)
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)

    def _init_tabs(self):
        self._tab_widget = QTabWidget()
        self.setCentralWidget(self._tab_widget)

        current = self._current_class()
        self._roll_call_tab = RollCallTab(current, self._repo)
        self._students_tab = StudentsTab(current, self._repo)
        self._records_tab = RecordsTab(current, self._repo)
        self._students_tab.students_changed.connect(self._on_students_changed)
        self._records_tab.records_changed.connect(self._roll_call_tab._refresh)

        self._tab_widget.addTab(self._roll_call_tab, "随机点名")
        self._tab_widget.addTab(self._students_tab, "学生管理")
        self._tab_widget.addTab(self._records_tab, "记录与统计")
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

    def _current_class(self) -> ClassData:
        idx = self._class_combo.currentIndex()
        if 0 <= idx < len(self._data.classes):
            return self._data.classes[idx]
        if self._data.classes:
            return self._data.classes[0]
        default = ClassData(id=str(uuid.uuid4()), name="默认班级")
        self._data.classes.append(default)
        self._repo.save()
        return default

    def _refresh_class_combo(self):
        selected_id = self._class_combo.currentData()
        self._current_class()
        self._class_combo.blockSignals(True)
        self._class_combo.clear()
        for c in self._data.classes:
            self._class_combo.addItem(c.name, c.id)
        selected_index = self._class_combo.findData(selected_id)
        if selected_index >= 0:
            self._class_combo.setCurrentIndex(selected_index)
        self._class_combo.blockSignals(False)
        self._on_class_changed(self._class_combo.currentIndex())

    def _on_class_changed(self, index: int):
        if index < 0 or index >= len(self._data.classes):
            return
        cls = self._data.classes[index]
        self._roll_call_tab.set_class_data(cls)
        self._students_tab.set_class_data(cls)
        self._records_tab.set_class_data(cls)

    def _on_tab_changed(self, index: int):
        if self._tab_widget.widget(index) is self._records_tab:
            self._records_tab._refresh()
        elif self._tab_widget.widget(index) is self._roll_call_tab:
            self._roll_call_tab._refresh()

    def _on_students_changed(self):
        self._roll_call_tab.set_class_data(self._current_class())
        self._records_tab._refresh()

    def _create_class(self):
        dlg = CreateClassDialog(self)
        if dlg.exec_() != CreateClassDialog.Accepted:
            return
        new_cls = ClassData(id=str(uuid.uuid4()), name=dlg.class_name())
        self._data.classes.append(new_cls)
        try:
            self._repo.save()
        except Exception as e:
            self._data.classes.remove(new_cls)
            QMessageBox.critical(self, "新建失败", str(e))
            return
        self._refresh_class_combo()
        self._class_combo.setCurrentIndex(len(self._data.classes) - 1)

    def _rename_class(self):
        idx = self._class_combo.currentIndex()
        if idx < 0:
            return
        cls = self._data.classes[idx]
        dlg = RenameClassDialog(cls.name, self)
        if dlg.exec_() != RenameClassDialog.Accepted:
            return
        try:
            with self._repo.edit_class(cls):
                cls.name = dlg.class_name()
        except Exception as e:
            QMessageBox.critical(self, "重命名失败", str(e))
            return
        self._class_combo.setItemText(idx, cls.name)

    def _delete_class(self):
        idx = self._class_combo.currentIndex()
        if idx < 0:
            return
        cls = self._data.classes[idx]
        dlg = DeleteClassDialog(cls.name, self)
        if dlg.exec_() != DeleteClassDialog.Accepted:
            return
        previous = list(self._data.classes)
        self._data.classes.pop(idx)
        if not self._data.classes:
            self._data.classes.append(ClassData(id=str(uuid.uuid4()), name="默认班级"))
        try:
            self._repo.save()
        except Exception as e:
            self._data.classes[:] = previous
            QMessageBox.critical(self, "删除失败", str(e))
            return
        self._refresh_class_combo()

    def _open_settings(self):
        dlg = SettingsDialog(self._repo.data_path, self)
        if dlg.exec_() != SettingsDialog.Accepted:
            return
        path = dlg.selected_path()
        if os.path.isfile(path) and os.path.abspath(path) != self._repo.data_path:
            if QMessageBox.question(
                self, "打开已有数据", "将载入所选文件中的班级、记录和轮次。当前数据保留在原文件中，是否继续？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            ) != QMessageBox.Yes:
                return
        try:
            self._repo.set_data_path(path)
        except Exception as e:
            QMessageBox.critical(self, "切换失败", f"仍使用原数据文件：\n{e}")
            return
        self._data = self._repo.data
        self._refresh_class_combo()
