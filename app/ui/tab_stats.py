from __future__ import annotations

# matplotlib 后端必须在 main.py 中 matplotlib.use("Agg") 之后才导入本模块
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams

rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "STHeiti", "Microsoft YaHei", "SimHei", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False

from PyQt5.QtWidgets import (
    QLabel, QPushButton, QVBoxLayout, QWidget,
)

from app.data.models import ClassData
from app.logic.statistics import calc_class_stats


class StatsTab(QWidget):
    def __init__(self, class_data: ClassData, parent=None):
        super().__init__(parent)
        self._class_data = class_data
        self._init_ui()
        self._refresh()

    def set_class_data(self, class_data: ClassData) -> None:
        self._class_data = class_data
        self._refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        refresh_btn = QPushButton("刷新图表")
        refresh_btn.clicked.connect(self._refresh)
        layout.addWidget(refresh_btn)

        self._fig = Figure(figsize=(8, 4), tight_layout=True)
        self._canvas = FigureCanvas(self._fig)
        layout.addWidget(self._canvas)

        self._summary_label = QLabel("")
        layout.addWidget(self._summary_label)

    def _refresh(self):
        self._fig.clear()
        stats = calc_class_stats(self._class_data.records)

        if not stats:
            ax = self._fig.add_subplot(111)
            ax.text(0.5, 0.5, "暂无记录", ha="center", va="center", transform=ax.transAxes)
            self._canvas.draw()
            self._summary_label.setText("")
            return

        names = [s["name"] for s in stats]
        counts = [s["count"] for s in stats]
        avgs = [s["avg_score"] for s in stats]

        ax = self._fig.add_subplot(111)
        bars = ax.bar(names, counts, color="#5B9BD5")
        ax.set_ylabel("点名次数")
        ax.set_title(f"{self._class_data.name} 点名次数分布")
        ax.tick_params(axis="x", rotation=45)

        for bar, avg in zip(bars, avgs):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                f"{avg}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

        self._canvas.draw()

        all_avgs = [s["avg_score"] for s in stats]
        self._summary_label.setText(
            f"平均分：{round(sum(all_avgs)/len(all_avgs), 1)}  "
            f"最高：{max(all_avgs)}  最低：{min(all_avgs)}"
        )
