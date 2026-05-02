import os
import sys


def get_app_dir() -> str:
    """用户数据目录：打包后为 exe 所在目录，开发时为项目根目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(rel: str) -> str:
    """内置资源路径：打包后从 _MEIPASS 读取，开发时从项目根目录读取。"""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


DEFAULT_DATA_FILENAME = "rollcall_data.json"
