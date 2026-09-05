import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QLockFile
from PyQt5.QtWidgets import QApplication, QMessageBox
import qdarktheme
import os

from app.config import get_app_dir, resource_path
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(qdarktheme.load_stylesheet("light"))
    app.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
    lock = QLockFile(os.path.join(get_app_dir(), "rollcall.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.warning(None, "无法启动", "程序已经运行，或程序目录不可写。请使用已打开的窗口，并检查目录权限。")
        return 1
    try:
        window = MainWindow()
    except Exception as e:
        QMessageBox.critical(None, "数据加载失败", f"为避免覆盖原数据，程序未启动。\n{e}")
        return 1
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
