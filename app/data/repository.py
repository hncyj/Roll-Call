from __future__ import annotations
import json
import os
import shutil
from contextlib import contextmanager
from copy import deepcopy
from typing import Optional

from app.config import get_app_dir, DEFAULT_DATA_FILENAME, SETTINGS_FILENAME
from app.data.models import AppData, ClassData
from app.data.migration import is_v1, migrate_v1_to_v2


class Repository:
    def __init__(self, data_path: Optional[str] = None):
        self._settings_path = os.path.join(get_app_dir(), SETTINGS_FILENAME)
        self._require_existing = False
        if data_path is None and os.path.exists(self._settings_path):
            with open(self._settings_path, encoding="utf-8") as f:
                data_path = json.load(f)["data_path"]
            if not isinstance(data_path, str) or not data_path.strip():
                raise ValueError("保存的数据路径无效，请检查 rollcall_settings.json。")
            if not os.path.isabs(data_path):
                data_path = os.path.join(get_app_dir(), data_path)
            self._require_existing = True
        self._data_path = os.path.abspath(data_path or os.path.join(get_app_dir(), DEFAULT_DATA_FILENAME))
        self._data: Optional[AppData] = None

    @property
    def data_path(self) -> str:
        return self._data_path

    @property
    def data(self) -> Optional[AppData]:
        return self._data

    def load(self) -> AppData:
        if not os.path.exists(self._data_path):
            if self._require_existing:
                raise FileNotFoundError(f"找不到已设置的数据文件：{self._data_path}。请连接原存储设备或恢复该文件。")
            self._data = AppData()
            return self._data
        with open(self._data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if is_v1(raw):
            bak = os.path.splitext(self._data_path)[0] + ".v1.bak.json"
            if not os.path.exists(bak):
                shutil.copy2(self._data_path, bak)
            raw = migrate_v1_to_v2(raw)
            migrated = True
        else:
            migrated = False
        if not isinstance(raw, dict) or raw.get("version") != 2 or not isinstance(raw.get("classes"), list):
            raise ValueError("不是受支持的点名数据文件（需要 version=2 和 classes 列表）。")
        self._data = AppData.from_dict(raw)
        if migrated:
            self.save()
        return self._data

    def save(self) -> None:
        if self._data is None:
            return
        self._write_json(self._data_path, self._data.to_dict())

    @staticmethod
    def _write_json(path: str, data: dict) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    @contextmanager
    def edit_class(self, class_data: ClassData):
        """保存失败时恢复原班级对象，避免界面继续使用未落盘的轮次。"""
        before = deepcopy(class_data.__dict__)
        try:
            yield
            self.save()
        except Exception:
            class_data.__dict__.update(before)
            raise

    def set_data_path(self, new_path: str) -> None:
        if not new_path.strip():
            raise ValueError("数据文件路径不能为空。")
        new_path = os.path.abspath(os.path.expanduser(new_path.strip()))
        if os.path.realpath(new_path) == os.path.realpath(self._settings_path):
            raise ValueError("不能用路径设置文件作为点名数据文件。")
        if new_path == self._data_path:
            return
        if self._data is None:
            raise ValueError("请先加载当前数据。")
        self.save()
        if os.path.exists(new_path):
            candidate = Repository(new_path)
            new_data = candidate.load()
        else:
            self._write_json(new_path, self._data.to_dict())
            new_data = self._data
        # 先持久化定位信息，成功后才切换内存中的路径和数据。
        stored_path = new_path
        if os.path.dirname(new_path) == os.path.abspath(get_app_dir()):
            stored_path = os.path.basename(new_path)
        self._write_json(self._settings_path, {"data_path": stored_path})
        self._data_path = new_path
        self._data = new_data
        self._require_existing = True
