from __future__ import annotations
import json
import os
import shutil
from typing import Optional

from app.config import get_app_dir, DEFAULT_DATA_FILENAME
from app.data.models import AppData
from app.data.migration import is_v1, migrate_v1_to_v2


class Repository:
    def __init__(self, data_path: Optional[str] = None):
        self._data_path = data_path or os.path.join(get_app_dir(), DEFAULT_DATA_FILENAME)
        self._data: Optional[AppData] = None

    @property
    def data_path(self) -> str:
        return self._data_path

    @property
    def data(self) -> Optional[AppData]:
        return self._data

    def load(self) -> AppData:
        if not os.path.exists(self._data_path):
            self._data = AppData()
            return self._data
        with open(self._data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if is_v1(raw):
            bak = self._data_path.replace(".json", ".v1.bak.json")
            shutil.copy2(self._data_path, bak)
            raw = migrate_v1_to_v2(raw)
        self._data = AppData.from_dict(raw)
        return self._data

    def save(self) -> None:
        if self._data is None:
            return
        os.makedirs(os.path.dirname(self._data_path) or ".", exist_ok=True)
        tmp = self._data_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data.to_dict(), f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._data_path)

    def set_data_path(self, new_path: str) -> None:
        self._data_path = new_path
        if self._data:
            self.save()
