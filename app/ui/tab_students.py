from __future__ import annotations

import openpyxl
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QHeaderView, QInputDialog,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from app.data.models import ClassData, Student
from app.data.repository import Repository

class StudentsTab(QWidget):
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
            wb = openpyxl.load_workbook(path)
            ws = wb.active
            students = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] is None or row[1] is None:
                    continue
                sid = str(row[0]).strip()
                name = str(row[1]).strip()
                if sid and name:
                    students.append(Student(id=sid, name=name))
            if not 1 <= len(students) <= 200:
                QMessageBox.warning(self, "错误", "学生人数必须在 1-200 人之间。")
                return
            self._class_data.students = students
            self._class_data.called_ids.clear()
            self._repo.save()
            self._refresh()
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
        self._class_data.students.append(Student(id=sid.strip(), name=name.strip()))
        self._repo.save()
        self._refresh()

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
        s.id = sid.strip()
        s.name = name.strip()
        self._repo.save()
        self._refresh()

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
        del self._class_data.students[row]
        self._repo.save()
        self._refresh()
