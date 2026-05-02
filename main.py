import sys
import matplotlib
matplotlib.use("Agg")

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
import qdarktheme

from app.config import resource_path
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(qdarktheme.load_stylesheet("light"))
    app.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
