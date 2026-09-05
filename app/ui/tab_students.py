from __future__ import annotations

import openpyxl
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QHeaderView, QInputDialog,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from app.data.models import ClassData, Student
from app.data.repository import Repository
from app.logic.students import edit_student, validate_students

class StudentsTab(QWidget):
    students_changed = pyqtSignal()

    def __init__(self, class_data: ClassData, repo: Repository, parent=None):
        super().__init__(parent)
        self._class_data = class_data
        self._repo = repo
        self._init_ui()
        self._refresh()

    def set_class_data(self, class_data: ClassData) -> None:
        self._class_data = class_data
        self._refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        import_btn = QPushButton("导入 Excel 名单")
        import_btn.clicked.connect(self._import_excel)
        add_btn = QPushButton("添加学生")
        add_btn.clicked.connect(self._add_student)
        edit_btn = QPushButton("修改选中")
        edit_btn.clicked.connect(self._edit_student)
        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self._delete_student)
        for btn in (import_btn, add_btn, edit_btn, del_btn):
            btn_row.addWidget(btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["学号", "姓名"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self._table)

    def _refresh(self):
        self._table.setRowCount(0)
        for s in self._class_data.students:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(s.id))
            self._table.setItem(row, 1, QTableWidgetItem(s.name))

    def _import_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 Excel 文件", "", "Excel Files (*.xlsx)")
        if not path:
            return
        try:
            wb = openpyxl.load_workbook(path, read_only=True)
            try:
                ws = wb.active
                students = []
                for number, row in enumerate(ws.iter_rows(min_row=2, max_col=2, values_only=True), 2):
                    if row[0] is None and row[1] is None:
                        continue
                    if row[0] is None or row[1] is None:
                        raise ValueError(f"第 {number} 行缺少学号或姓名。")
                    students.append(Student(id=str(row[0]).strip(), name=str(row[1]).strip()))
            finally:
                wb.close()
            if not 1 <= len(students) <= 200:
                QMessageBox.warning(self, "错误", "学生人数必须在 1-200 人之间。")
                return
            validate_students(students)
            if self._class_data.students and QMessageBox.question(
                self, "替换名单", "将替换当前学生名单，历史评分和本轮已点名状态保留。是否继续？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            ) != QMessageBox.Yes:
                return
            with self._repo.edit_class(self._class_data):
                self._class_data.students = students
            self._refresh()
            self.students_changed.emit()
            QMessageBox.information(self, "成功", f"成功导入 {len(students)} 名学生。")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", str(e))

    def _add_student(self):
        sid, ok1 = QInputDialog.getText(self, "添加学生", "学号：")
        if not ok1 or not sid.strip():
            return
        name, ok2 = QInputDialog.getText(self, "添加学生", "姓名：")
        if not ok2 or not name.strip():
            return
        try:
            students = self._class_data.students + [Student(id=sid.strip(), name=name.strip())]
            validate_students(students)
            with self._repo.edit_class(self._class_data):
                self._class_data.students = students
        except Exception as e:
            QMessageBox.warning(self, "添加失败", str(e))
            return
        self._refresh()
        self.students_changed.emit()

    def _edit_student(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一名学生。")
            return
        s = self._class_data.students[row]
        sid, ok1 = QInputDialog.getText(self, "修改学生", "学号：", text=s.id)
        if not ok1:
            return
        name, ok2 = QInputDialog.getText(self, "修改学生", "姓名：", text=s.name)
        if not ok2:
            return
        try:
            with self._repo.edit_class(self._class_data):
                edit_student(self._class_data, s, sid, name)
        except Exception as e:
            QMessageBox.warning(self, "修改失败", str(e))
            return
        self._refresh()
        self.students_changed.emit()

    def _delete_student(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一名学生。")
            return
        s = self._class_data.students[row]
        reply = QMessageBox.question(
            self, "确认删除", f"确认删除学生 {s.name}？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            with self._repo.edit_class(self._class_data):
                del self._class_data.students[row]
        except Exception as e:
            QMessageBox.critical(self, "删除失败", str(e))
            return
        self._refresh()
        self.students_changed.emit()
