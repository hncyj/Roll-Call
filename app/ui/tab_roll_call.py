from __future__ import annotations
import datetime

from PyQt5.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QListWidget, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from app.data.models import ClassData, Record, Student
from app.data.repository import Repository
from app.logic.roll_call import RollCallEngine
from app.logic.statistics import calc_class_stats
from app.ui.widgets.animation_widget import AnimationWidget


class RollCallTab(QWidget):
    def __init__(self, class_data: ClassData, repo: Repository, parent=None):
        super().__init__(parent)
        self._class_data = class_data
        self._repo = repo
        self._engine = RollCallEngine(class_data)
        self._selected_student: Student | None = None
        self._init_ui()
        self._refresh()

    def set_class_data(self, class_data: ClassData) -> None:
        self._class_data = class_data
        self._engine = RollCallEngine(class_data)
        self._selected_student = None
        self._animation.set_text("--")
        self._refresh()

    def _init_ui(self):
        root = QHBoxLayout(self)

        # ── 左侧：点名操作区（2/3）──
        left = QVBoxLayout()

        self._animation = AnimationWidget()
        self._animation.animation_finished.connect(self._on_animation_done)
        left.addWidget(self._animation, stretch=1)

        btn_row = QHBoxLayout()
        self._random_btn = QPushButton("随机点名")
        self._random_btn.clicked.connect(self._random_roll)
        self._manual_btn = QPushButton("手动点名")
        self._manual_btn.clicked.connect(self._manual_roll)
        btn_row.addWidget(self._random_btn)
        btn_row.addWidget(self._manual_btn)
        left.addLayout(btn_row)

        score_row = QHBoxLayout()
        score_row.addWidget(QLabel("评分（0-100）："))
        self._score_spin = QSpinBox()
        self._score_spin.setRange(0, 100)
        self._score_spin.setValue(60)
        score_row.addWidget(self._score_spin)
        self._save_btn = QPushButton("保存本次记录")
        self._save_btn.clicked.connect(self._save_record)
        score_row.addWidget(self._save_btn)
        score_row.addStretch()
        left.addLayout(score_row)

        left.addWidget(QLabel("学生名单（手动点名用）："))
        self._student_list = QListWidget()
        left.addWidget(self._student_list, stretch=2)

        self._reset_btn = QPushButton("重置轮询")
        self._reset_btn.clicked.connect(self._reset_called)
        left.addWidget(self._reset_btn)

        root.addLayout(left, stretch=2)

        # ── 右侧：点名次数统计（1/3）──
        right = QVBoxLayout()
        right.addWidget(QLabel("点名次数统计"))
        self._count_table = QTableWidget(0, 3)
        self._count_table.setHorizontalHeaderLabels(["学号", "姓名", "次数"])
        self._count_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._count_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._count_table.setSelectionBehavior(QTableWidget.SelectRows)
        right.addWidget(self._count_table)

        root.addLayout(right, stretch=1)

    def _random_roll(self):
        if self._animation.is_animating:
            return
        student = self._engine.pick_random()
        if student is None:
            reply = QMessageBox.question(
                self, "全部点完", "本班所有学生已全部点名完毕，是否重置？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self._engine.reset()
                self._repo.save()
                self._refresh()
            return
        names = [s.name for s in self._class_data.students]
        self._random_btn.setEnabled(False)
        self._manual_btn.setEnabled(False)
        self._animation.start(names, student)

    def _on_animation_done(self, student: Student):
        self._selected_student = student
        self._random_btn.setEnabled(True)
        self._manual_btn.setEnabled(True)

    def _manual_roll(self):
        item = self._student_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "提示", "请先在名单中选中一名学生。")
            return
        idx = self._student_list.currentRow()
        if idx < len(self._class_data.students):
            self._selected_student = self._class_data.students[idx]
            self._animation.set_text(self._selected_student.name)

    def _save_record(self):
        if self._selected_student is None:
            QMessageBox.warning(self, "提示", "请先点名。")
            return
        record = Record(
            student_id=self._selected_student.id,
            name=self._selected_student.name,
            time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            score=self._score_spin.value(),
        )
        self._class_data.records.append(record)
        self._engine.mark_called(self._selected_student.id)
        self._repo.save()
        self._refresh()
        QMessageBox.information(self, "成功", "记录已保存。")

    def _reset_called(self):
        self._engine.reset()
        self._repo.save()
        self._refresh()

    def _refresh(self):
        self._student_list.clear()
        for s in self._class_data.students:
            self._student_list.addItem(f"{s.id}  {s.name}")

        counts = {s["student_id"]: s["count"] for s in calc_class_stats(self._class_data.records)}
        self._count_table.setRowCount(0)
        for s in self._class_data.students:
            row = self._count_table.rowCount()
            self._count_table.insertRow(row)
            self._count_table.setItem(row, 0, QTableWidgetItem(s.id))
            self._count_table.setItem(row, 1, QTableWidgetItem(s.name))
            self._count_table.setItem(row, 2, QTableWidgetItem(str(counts.get(s.id, 0))))
