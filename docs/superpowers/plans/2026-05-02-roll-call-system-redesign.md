> 历史方案存档：本文记录 2026-05-02 的设计或实施计划，不是当前验收标准。当前功能、点名轮次和数据路径规则请以 [README](../../../README.md) 及现有代码为准。缺席 / 请假与独立图表页不属于当前功能。

# 随机点名系统 重构 & 功能扩展 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有单文件随机点名系统重构为分层架构，修复全部已知 Bug，并新增班级管理、点名动画、缺席标记、统计图表等功能，最终打包为兼容 Win7+ 的单 exe。

**Architecture:** 渐进式重构，分三层：`data`（JSON 读写 + 迁移）、`logic`（业务逻辑，无 UI 依赖）、`ui`（PyQt5 界面，每 Tab 独立文件）。Repository 负责 v1→v2 自动迁移并做原子写保护。所有 Tab 持有同一 ClassData 引用，修改后调用 `repo.save()` 落盘。

**Tech Stack:** Python 3.x, PyQt5 ≥ 5.15, pyqtdarktheme (light), matplotlib, openpyxl, PyInstaller

---

## 文件清单

| 路径 | 职责 |
|------|------|
| `main.py` | 入口，~10 行 |
| `app/__init__.py` | 包标记 |
| `app/config.py` | `get_app_dir()`、路径常量 |
| `app/data/__init__.py` | 包标记 |
| `app/data/models.py` | 数据类：Student / Record / ClassData / AppData |
| `app/data/migration.py` | v1 → v2 迁移逻辑 |
| `app/data/repository.py` | JSON 读写、原子写、路径管理 |
| `app/logic/__init__.py` | 包标记 |
| `app/logic/roll_call.py` | RollCallEngine |
| `app/logic/statistics.py` | calc_class_stats() |
| `app/ui/__init__.py` | 包标记 |
| `app/ui/main_window.py` | 主窗口、班级工具栏、Tab 容器 |
| `app/ui/tab_roll_call.py` | 随机点名 Tab |
| `app/ui/tab_students.py` | 学生管理 Tab |
| `app/ui/tab_records.py` | 记录查询 Tab |
| `app/ui/tab_stats.py` | 统计图表 Tab |
| `app/ui/dialogs/__init__.py` | 包标记 |
| `app/ui/dialogs/class_dialog.py` | 新建/重命名/删除班级对话框 |
| `app/ui/dialogs/settings_dialog.py` | 数据路径设置对话框 |
| `app/ui/widgets/__init__.py` | 包标记 |
| `app/ui/widgets/animation_widget.py` | 抽签滚动动画 |
| `app/ui/widgets/status_panel.py` | 已点/未点状态面板 |
| `tests/__init__.py` | 包标记 |
| `tests/data/test_models.py` | 模型单元测试 |
| `tests/data/test_migration.py` | 迁移逻辑测试 |
| `tests/data/test_repository.py` | Repository 测试 |
| `tests/logic/test_roll_call.py` | RollCallEngine 测试 |
| `tests/logic/test_statistics.py` | 统计逻辑测试 |
| `tests/fixtures/v1_data.json` | v1 格式测试用夹具 |
| `requirements.txt` | 运行依赖 |
| `requirements-dev.txt` | 开发依赖（pytest） |

---

## Task 1: 项目脚手架

**Files:**
- Create: 所有目录和空文件（见文件清单）
- Create: `requirements.txt`
- Create: `requirements-dev.txt`

- [ ] **Step 1: 创建目录结构**

```bash
cd /Users/yinjiechen/Documents/GitLab/order_name
mkdir -p app/data app/logic app/ui/dialogs app/ui/widgets
mkdir -p tests/data tests/logic tests/fixtures
```

- [ ] **Step 2: 创建所有 `__init__.py` 文件**

```bash
touch app/__init__.py app/data/__init__.py app/logic/__init__.py
touch app/ui/__init__.py app/ui/dialogs/__init__.py app/ui/widgets/__init__.py
touch tests/__init__.py tests/data/__init__.py tests/logic/__init__.py
```

- [ ] **Step 3: 创建 `requirements.txt`**

写入内容：
```
PyQt5>=5.15
pyqtdarktheme
matplotlib
openpyxl
```

- [ ] **Step 4: 创建 `requirements-dev.txt`**

写入内容：
```
pytest
```

- [ ] **Step 5: 安装依赖**

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

预期：无报错，所有包安装成功。

- [ ] **Step 6: 提交**

```bash
git init
git add requirements.txt requirements-dev.txt app/ tests/
git commit -m "chore: scaffold project structure"
```

---

## Task 2: 数据模型

**Files:**
- Create: `app/data/models.py`
- Create: `tests/data/test_models.py`

- [ ] **Step 1: 编写失败测试**

`tests/data/test_models.py`:
```python
import pytest
from app.data.models import Student, Record, ClassData, AppData


def test_student_defaults():
    s = Student(id="001", name="张三")
    assert s.status == "normal"


def test_student_round_trip():
    s = Student(id="001", name="张三", status="absent")
    assert Student.from_dict(s.to_dict()) == s


def test_student_from_dict_coerces_int_id():
    s = Student.from_dict({"id": 2541123101, "name": "曾璟宁"})
    assert s.id == "2541123101"
    assert s.status == "normal"


def test_record_round_trip():
    r = Record(student_id="001", name="张三", time="2026-05-02 10:00:00", score=85)
    assert Record.from_dict(r.to_dict()) == r


def test_record_from_dict_legacy_id_field():
    # v1 records use "id" instead of "student_id"
    r = Record.from_dict({"id": "001", "name": "张三", "time": "2026-05-02", "score": 80})
    assert r.student_id == "001"


def test_class_data_round_trip():
    c = ClassData(id="cls_001", name="工商管理班")
    c.students.append(Student(id="001", name="张三"))
    c.called_ids.append("001")
    restored = ClassData.from_dict(c.to_dict())
    assert restored.id == c.id
    assert restored.name == c.name
    assert restored.students[0] == c.students[0]
    assert restored.called_ids == c.called_ids


def test_app_data_round_trip():
    app = AppData()
    app.classes.append(ClassData(id="cls_001", name="工商管理班"))
    restored = AppData.from_dict(app.to_dict())
    assert restored.version == 2
    assert restored.classes[0].name == "工商管理班"
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/data/test_models.py -v
```

预期：`ModuleNotFoundError: No module named 'app.data.models'`

- [ ] **Step 3: 实现 `app/data/models.py`**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class Student:
    id: str
    name: str
    status: str = "normal"  # normal | absent | leave

    @classmethod
    def from_dict(cls, d: dict) -> Student:
        return cls(id=str(d["id"]), name=d["name"], status=d.get("status", "normal"))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "status": self.status}


@dataclass
class Record:
    student_id: str
    name: str
    time: str
    score: int
    status: str = "normal"

    @classmethod
    def from_dict(cls, d: dict) -> Record:
        return cls(
            student_id=str(d.get("student_id", d.get("id", ""))),
            name=d["name"],
            time=d["time"],
            score=int(d["score"]),
            status=d.get("status", "normal"),
        )

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "time": self.time,
            "score": self.score,
            "status": self.status,
        }


@dataclass
class ClassData:
    id: str
    name: str
    students: List[Student] = field(default_factory=list)
    records: List[Record] = field(default_factory=list)
    called_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> ClassData:
        return cls(
            id=d["id"],
            name=d["name"],
            students=[Student.from_dict(s) for s in d.get("students", [])],
            records=[Record.from_dict(r) for r in d.get("records", [])],
            called_ids=[str(i) for i in d.get("called_ids", [])],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "students": [s.to_dict() for s in self.students],
            "records": [r.to_dict() for r in self.records],
            "called_ids": self.called_ids,
        }


@dataclass
class AppData:
    version: int = 2
    classes: List[ClassData] = field(default_factory=list)
    settings: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> AppData:
        return cls(
            version=d.get("version", 2),
            classes=[ClassData.from_dict(c) for c in d.get("classes", [])],
            settings=d.get("settings", {}),
        )

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "classes": [c.to_dict() for c in self.classes],
            "settings": self.settings,
        }
```

- [ ] **Step 4: 运行测试，确认全部通过**

```bash
pytest tests/data/test_models.py -v
```

预期：7 个测试全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add app/data/models.py tests/data/test_models.py
git commit -m "feat: add data models with serialization"
```

---

## Task 3: 数据迁移

**Files:**
- Create: `app/data/migration.py`
- Create: `tests/fixtures/v1_data.json`
- Create: `tests/data/test_migration.py`

- [ ] **Step 1: 创建 v1 格式测试夹具**

`tests/fixtures/v1_data.json`:
```json
{
  "classes": ["工商管理班", "市场营销班"],
  "students": {
    "工商管理班": [
      {"id": "2541123101", "name": "曾璟宁"},
      {"id": "2541123102", "name": "黄佳琪"}
    ],
    "市场营销班": [
      {"id": "2541121101", "name": "吴浩勇"}
    ]
  },
  "records": {
    "工商管理班": [
      {"id": "2541123101", "name": "曾璟宁", "time": "2026-05-01 09:00:00", "score": 85}
    ],
    "市场营销班": []
  },
  "called_students": {
    "工商管理班": [{"id": "2541123101", "name": "曾璟宁"}],
    "市场营销班": []
  }
}
```

- [ ] **Step 2: 编写失败测试**

`tests/data/test_migration.py`:
```python
import json
import os
import pytest
from app.data.migration import is_v1, migrate_v1_to_v2

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "../fixtures/v1_data.json")


@pytest.fixture
def v1_raw():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_is_v1_detects_missing_version(v1_raw):
    assert is_v1(v1_raw) is True


def test_is_v1_returns_false_for_v2():
    assert is_v1({"version": 2, "classes": []}) is False


def test_migrate_produces_version_2(v1_raw):
    result = migrate_v1_to_v2(v1_raw)
    assert result["version"] == 2


def test_migrate_class_count(v1_raw):
    result = migrate_v1_to_v2(v1_raw)
    assert len(result["classes"]) == 2


def test_migrate_class_names(v1_raw):
    result = migrate_v1_to_v2(v1_raw)
    names = [c["name"] for c in result["classes"]]
    assert "工商管理班" in names
    assert "市场营销班" in names


def test_migrate_students(v1_raw):
    result = migrate_v1_to_v2(v1_raw)
    cls = next(c for c in result["classes"] if c["name"] == "工商管理班")
    assert len(cls["students"]) == 2
    assert cls["students"][0]["id"] == "2541123101"
    assert cls["students"][0]["status"] == "normal"


def test_migrate_records(v1_raw):
    result = migrate_v1_to_v2(v1_raw)
    cls = next(c for c in result["classes"] if c["name"] == "工商管理班")
    assert len(cls["records"]) == 1
    r = cls["records"][0]
    assert r["student_id"] == "2541123101"
    assert r["status"] == "normal"
    assert "id" not in r


def test_migrate_called_ids(v1_raw):
    result = migrate_v1_to_v2(v1_raw)
    cls = next(c for c in result["classes"] if c["name"] == "工商管理班")
    assert cls["called_ids"] == ["2541123101"]


def test_migrate_class_ids_are_strings(v1_raw):
    result = migrate_v1_to_v2(v1_raw)
    for cls in result["classes"]:
        assert isinstance(cls["id"], str)
        assert cls["id"].startswith("cls_")
```

- [ ] **Step 3: 运行测试，确认失败**

```bash
pytest tests/data/test_migration.py -v
```

预期：`ModuleNotFoundError: No module named 'app.data.migration'`

- [ ] **Step 4: 实现 `app/data/migration.py`**

```python
from __future__ import annotations
from typing import Any, Dict


def is_v1(raw: Dict[str, Any]) -> bool:
    return "version" not in raw


def migrate_v1_to_v2(raw: Dict[str, Any]) -> Dict[str, Any]:
    class_names = raw.get("classes", [])
    students_map = raw.get("students", {})
    records_map = raw.get("records", {})
    called_map = raw.get("called_students", {})

    classes = []
    for i, name in enumerate(class_names):
        students = [
            {"id": str(s["id"]), "name": s["name"], "status": "normal"}
            for s in students_map.get(name, [])
        ]
        called_ids = [str(s["id"]) for s in called_map.get(name, [])]
        records = [
            {
                "student_id": str(r.get("id", r.get("student_id", ""))),
                "name": r["name"],
                "time": r["time"],
                "score": r["score"],
                "status": "normal",
            }
            for r in records_map.get(name, [])
        ]
        classes.append({
            "id": f"cls_{i:03d}",
            "name": name,
            "students": students,
            "records": records,
            "called_ids": called_ids,
        })

    return {"version": 2, "classes": classes, "settings": {}}
```

- [ ] **Step 5: 运行测试，确认全部通过**

```bash
pytest tests/data/test_migration.py -v
```

预期：9 个测试全部 PASS。

- [ ] **Step 6: 提交**

```bash
git add app/data/migration.py tests/data/test_migration.py tests/fixtures/v1_data.json
git commit -m "feat: add v1->v2 migration logic"
```

---

## Task 4: Config + Repository

**Files:**
- Create: `app/config.py`
- Create: `app/data/repository.py`
- Create: `tests/data/test_repository.py`

- [ ] **Step 1: 编写失败测试**

`tests/data/test_repository.py`:
```python
import json
import os
import pytest
from app.data.repository import Repository
from app.data.models import AppData, ClassData, Student


@pytest.fixture
def tmp_repo(tmp_path):
    repo = Repository(data_path=str(tmp_path / "data.json"))
    return repo


@pytest.fixture
def v1_repo(tmp_path):
    v1 = {
        "classes": ["工商管理班"],
        "students": {"工商管理班": [{"id": "001", "name": "张三"}]},
        "records": {"工商管理班": []},
        "called_students": {"工商管理班": []},
    }
    p = tmp_path / "data.json"
    p.write_text(json.dumps(v1), encoding="utf-8")
    return Repository(data_path=str(p))


def test_load_empty_creates_default(tmp_repo):
    data = tmp_repo.load()
    assert isinstance(data, AppData)
    assert data.version == 2


def test_save_and_reload(tmp_repo):
    data = tmp_repo.load()
    data.classes.append(ClassData(id="cls_001", name="工商管理班"))
    tmp_repo.save()

    repo2 = Repository(data_path=tmp_repo.data_path)
    data2 = repo2.load()
    assert len(data2.classes) == 1
    assert data2.classes[0].name == "工商管理班"


def test_save_is_atomic(tmp_repo):
    data = tmp_repo.load()
    data.classes.append(ClassData(id="cls_001", name="工商管理班"))
    tmp_repo.save()
    assert not os.path.exists(tmp_repo.data_path + ".tmp")


def test_v1_auto_migrates(v1_repo):
    data = v1_repo.load()
    assert data.version == 2
    assert len(data.classes) == 1
    assert data.classes[0].students[0].id == "001"


def test_v1_creates_backup(tmp_path, v1_repo):
    v1_repo.load()
    bak = str(tmp_path / "data.v1.bak.json")
    assert os.path.exists(bak)


def test_set_data_path(tmp_repo, tmp_path):
    tmp_repo.load()
    new_path = str(tmp_path / "subdir" / "data.json")
    tmp_repo.set_data_path(new_path)
    assert tmp_repo.data_path == new_path
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/data/test_repository.py -v
```

预期：`ModuleNotFoundError: No module named 'app.data.repository'`

- [ ] **Step 3: 实现 `app/config.py`**

```python
import os
import sys


def get_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULT_DATA_FILENAME = "roll_call_data.json"
```

- [ ] **Step 4: 实现 `app/data/repository.py`**

```python
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
```

- [ ] **Step 5: 运行测试，确认全部通过**

```bash
pytest tests/data/test_repository.py -v
```

预期：6 个测试全部 PASS。

- [ ] **Step 6: 运行所有已有测试**

```bash
pytest tests/ -v
```

预期：全部 PASS，无回归。

- [ ] **Step 7: 提交**

```bash
git add app/config.py app/data/repository.py tests/data/test_repository.py
git commit -m "feat: add config and repository with atomic write and auto-migration"
```

---

## Task 5: 点名逻辑

**Files:**
- Create: `app/logic/roll_call.py`
- Create: `tests/logic/test_roll_call.py`

- [ ] **Step 1: 编写失败测试**

`tests/logic/test_roll_call.py`:
```python
import pytest
from app.data.models import ClassData, Student
from app.logic.roll_call import RollCallEngine


@pytest.fixture
def class_with_students():
    c = ClassData(id="cls_001", name="工商管理班")
    c.students = [
        Student(id="001", name="张三"),
        Student(id="002", name="李四"),
        Student(id="003", name="王五", status="absent"),
        Student(id="004", name="赵六", status="leave"),
    ]
    return c


def test_get_uncalled_excludes_absent_and_leave(class_with_students):
    engine = RollCallEngine(class_with_students)
    uncalled = engine.get_uncalled()
    ids = [s.id for s in uncalled]
    assert "001" in ids
    assert "002" in ids
    assert "003" not in ids
    assert "004" not in ids


def test_get_uncalled_excludes_already_called(class_with_students):
    class_with_students.called_ids.append("001")
    engine = RollCallEngine(class_with_students)
    ids = [s.id for s in engine.get_uncalled()]
    assert "001" not in ids
    assert "002" in ids


def test_get_called_returns_called_students(class_with_students):
    class_with_students.called_ids.append("001")
    engine = RollCallEngine(class_with_students)
    called = engine.get_called()
    assert len(called) == 1
    assert called[0].id == "001"


def test_pick_random_returns_uncalled_student(class_with_students):
    engine = RollCallEngine(class_with_students)
    student = engine.pick_random()
    assert student is not None
    assert student.id in ["001", "002"]


def test_pick_random_returns_none_when_complete(class_with_students):
    class_with_students.called_ids = ["001", "002"]
    engine = RollCallEngine(class_with_students)
    assert engine.pick_random() is None


def test_mark_called(class_with_students):
    engine = RollCallEngine(class_with_students)
    engine.mark_called("001")
    assert "001" in class_with_students.called_ids


def test_mark_called_no_duplicate(class_with_students):
    engine = RollCallEngine(class_with_students)
    engine.mark_called("001")
    engine.mark_called("001")
    assert class_with_students.called_ids.count("001") == 1


def test_reset_clears_called_ids(class_with_students):
    class_with_students.called_ids = ["001", "002"]
    engine = RollCallEngine(class_with_students)
    engine.reset()
    assert class_with_students.called_ids == []


def test_is_complete_false_when_uncalled_exist(class_with_students):
    engine = RollCallEngine(class_with_students)
    assert engine.is_complete() is False


def test_is_complete_true_when_all_called(class_with_students):
    class_with_students.called_ids = ["001", "002"]
    engine = RollCallEngine(class_with_students)
    assert engine.is_complete() is True


def test_reset_does_not_change_student_status(class_with_students):
    class_with_students.called_ids = ["001"]
    engine = RollCallEngine(class_with_students)
    engine.reset()
    assert class_with_students.students[2].status == "absent"
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/logic/test_roll_call.py -v
```

预期：`ModuleNotFoundError: No module named 'app.logic.roll_call'`

- [ ] **Step 3: 实现 `app/logic/roll_call.py`**

```python
from __future__ import annotations
import random
from typing import List, Optional

from app.data.models import ClassData, Student


class RollCallEngine:
    def __init__(self, class_data: ClassData):
        self._class_data = class_data

    def get_uncalled(self) -> List[Student]:
        called_set = set(self._class_data.called_ids)
        return [
            s for s in self._class_data.students
            if s.status == "normal" and s.id not in called_set
        ]

    def get_called(self) -> List[Student]:
        called_set = set(self._class_data.called_ids)
        return [s for s in self._class_data.students if s.id in called_set]

    def pick_random(self) -> Optional[Student]:
        uncalled = self.get_uncalled()
        if not uncalled:
            return None
        return random.choice(uncalled)

    def mark_called(self, student_id: str) -> None:
        if student_id not in self._class_data.called_ids:
            self._class_data.called_ids.append(student_id)

    def reset(self) -> None:
        self._class_data.called_ids.clear()

    def is_complete(self) -> bool:
        return len(self.get_uncalled()) == 0
```

- [ ] **Step 4: 运行测试，确认全部通过**

```bash
pytest tests/logic/test_roll_call.py -v
```

预期：11 个测试全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add app/logic/roll_call.py tests/logic/test_roll_call.py
git commit -m "feat: add RollCallEngine with round-robin and status filtering"
```

---

## Task 6: 统计逻辑

**Files:**
- Create: `app/logic/statistics.py`
- Create: `tests/logic/test_statistics.py`

- [ ] **Step 1: 编写失败测试**

`tests/logic/test_statistics.py`:
```python
import pytest
from app.data.models import Record
from app.logic.statistics import calc_class_stats


@pytest.fixture
def records():
    return [
        Record(student_id="001", name="张三", time="2026-05-01 09:00:00", score=80),
        Record(student_id="001", name="张三", time="2026-05-02 09:00:00", score=90),
        Record(student_id="002", name="李四", time="2026-05-01 09:00:00", score=70),
        Record(student_id="003", name="张三", time="2026-05-01 09:00:00", score=60),
        # 注意：id=003 的学生姓名也是"张三"，旧版会合并，新版按 student_id 区分
    ]


def test_calc_counts(records):
    stats = calc_class_stats(records)
    entry_001 = next(s for s in stats if s["student_id"] == "001")
    assert entry_001["count"] == 2


def test_calc_avg_score(records):
    stats = calc_class_stats(records)
    entry_001 = next(s for s in stats if s["student_id"] == "001")
    assert entry_001["avg_score"] == 85.0


def test_different_ids_same_name_not_merged(records):
    stats = calc_class_stats(records)
    zhang_entries = [s for s in stats if s["name"] == "张三"]
    assert len(zhang_entries) == 2  # 001 和 003 分开统计


def test_empty_records():
    assert calc_class_stats([]) == []


def test_result_sorted_by_name(records):
    stats = calc_class_stats(records)
    names = [s["name"] for s in stats]
    assert names == sorted(names)
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/logic/test_statistics.py -v
```

预期：`ModuleNotFoundError: No module named 'app.logic.statistics'`

- [ ] **Step 3: 实现 `app/logic/statistics.py`**

```python
from __future__ import annotations
from typing import Dict, List

from app.data.models import Record


def calc_class_stats(records: List[Record]) -> List[Dict]:
    stat: Dict[str, Dict] = {}
    for r in records:
        if r.student_id not in stat:
            stat[r.student_id] = {
                "student_id": r.student_id,
                "name": r.name,
                "count": 0,
                "total": 0,
            }
        stat[r.student_id]["count"] += 1
        stat[r.student_id]["total"] += r.score
    result = [
        {
            "student_id": v["student_id"],
            "name": v["name"],
            "count": v["count"],
            "avg_score": round(v["total"] / v["count"], 1),
        }
        for v in stat.values()
    ]
    return sorted(result, key=lambda x: x["name"])
```

- [ ] **Step 4: 运行测试，确认全部通过**

```bash
pytest tests/logic/test_statistics.py -v
```

预期：5 个测试全部 PASS。

- [ ] **Step 5: 运行全套测试**

```bash
pytest tests/ -v
```

预期：全部 PASS。

- [ ] **Step 6: 提交**

```bash
git add app/logic/statistics.py tests/logic/test_statistics.py
git commit -m "feat: add statistics calculation aggregated by student_id"
```

---

## Task 7: 动画 Widget

**Files:**
- Create: `app/ui/widgets/animation_widget.py`

- [ ] **Step 1: 实现 `app/ui/widgets/animation_widget.py`**

```python
from __future__ import annotations
import random
from typing import List

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class AnimationWidget(QWidget):
    animation_finished = pyqtSignal(object)  # emits Student

    _INTERVALS = [50, 50, 50, 50, 80, 80, 120, 150, 200, 280, 350, 400]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._label = QLabel("--")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("font-size: 36px; font-weight: bold; padding: 20px;")
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._names: List[str] = []
        self._target = None
        self._step = 0

    def start(self, names: List[str], target) -> None:
        """Start animation. target is the Student that will be shown at the end."""
        self._names = names
        self._target = target
        self._step = 0
        self._timer.start(self._INTERVALS[0])

    def _tick(self) -> None:
        self._step += 1
        if self._step >= len(self._INTERVALS):
            self._timer.stop()
            self._label.setText(self._target.name)
            self.animation_finished.emit(self._target)
            return
        self._label.setText(random.choice(self._names))
        self._timer.start(self._INTERVALS[self._step])

    def set_text(self, text: str) -> None:
        self._label.setText(text)

    @property
    def is_animating(self) -> bool:
        return self._timer.isActive()
```

- [ ] **Step 2: 手动验证（无自动化 UI 测试）**

AnimationWidget 需要 QApplication，在 Task 11（Roll Call Tab）集成后随整体窗口测试。

- [ ] **Step 3: 提交**

```bash
git add app/ui/widgets/animation_widget.py
git commit -m "feat: add animation widget with exponential slowdown"
```

---

## Task 8: 状态面板 Widget

**Files:**
- Create: `app/ui/widgets/status_panel.py`

- [ ] **Step 1: 实现 `app/ui/widgets/status_panel.py`**

```python
from __future__ import annotations
from typing import List

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGroupBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from app.data.models import Student


_STATUS_LABEL = {"absent": "（缺席）", "leave": "（请假）", "normal": ""}
_STATUS_COLOR = {"absent": QColor(180, 50, 50), "leave": QColor(180, 120, 0)}


class StatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._called_label = QLabel("已点名（0）")
        self._called_list = QListWidget()
        called_group = QGroupBox()
        called_layout = QVBoxLayout(called_group)
        called_layout.addWidget(self._called_label)
        called_layout.addWidget(self._called_list)

        self._uncalled_label = QLabel("未点名（0）")
        self._uncalled_list = QListWidget()
        uncalled_group = QGroupBox()
        uncalled_layout = QVBoxLayout(uncalled_group)
        uncalled_layout.addWidget(self._uncalled_label)
        uncalled_layout.addWidget(self._uncalled_list)

        layout.addWidget(called_group)
        layout.addWidget(uncalled_group)

    def refresh(self, called: List[Student], uncalled: List[Student]) -> None:
        self._called_label.setText(f"已点名（{len(called)}）")
        self._called_list.clear()
        for s in called:
            self._called_list.addItem(f"{s.id}  {s.name}")

        self._uncalled_label.setText(f"未点名（{len(uncalled)}）")
        self._uncalled_list.clear()
        for s in uncalled:
            suffix = _STATUS_LABEL.get(s.status, "")
            item = QListWidgetItem(f"{s.id}  {s.name}{suffix}")
            if s.status in _STATUS_COLOR:
                item.setForeground(_STATUS_COLOR[s.status])
            self._uncalled_list.addItem(item)
```

- [ ] **Step 2: 提交**

```bash
git add app/ui/widgets/status_panel.py
git commit -m "feat: add status panel widget showing called/uncalled students"
```

---

## Task 9: 班级 & 设置对话框

**Files:**
- Create: `app/ui/dialogs/class_dialog.py`
- Create: `app/ui/dialogs/settings_dialog.py`

- [ ] **Step 1: 实现 `app/ui/dialogs/class_dialog.py`**

```python
from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QLabel, QLineEdit, QVBoxLayout,
)


class CreateClassDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建班级")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("班级名称："))
        self._edit = QLineEdit()
        layout.addWidget(self._edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def class_name(self) -> str:
        return self._edit.text().strip()

    def accept(self):
        if self.class_name():
            super().accept()


class RenameClassDialog(QDialog):
    def __init__(self, old_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("重命名班级")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("新班级名称："))
        self._edit = QLineEdit(old_name)
        self._edit.selectAll()
        layout.addWidget(self._edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def class_name(self) -> str:
        return self._edit.text().strip()

    def accept(self):
        if self.class_name():
            super().accept()


class DeleteClassDialog(QDialog):
    def __init__(self, class_name: str, parent=None):
        super().__init__(parent)
        self._expected = class_name
        self.setWindowTitle("删除班级")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'此操作不可恢复。\n请输入班级名称 "{class_name}" 确认删除：'))
        self._edit = QLineEdit()
        layout.addWidget(self._edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        if self._edit.text().strip() == self._expected:
            super().accept()
```

- [ ] **Step 2: 实现 `app/ui/dialogs/settings_dialog.py`**

```python
from __future__ import annotations
import os

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

from app.config import get_app_dir, DEFAULT_DATA_FILENAME


class SettingsDialog(QDialog):
    def __init__(self, current_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("数据文件路径："))

        path_row = QHBoxLayout()
        self._edit = QLineEdit(current_path)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse)
        default_btn = QPushButton("恢复默认")
        default_btn.clicked.connect(self._restore_default)
        path_row.addWidget(self._edit)
        path_row.addWidget(browse_btn)
        path_row.addWidget(default_btn)
        layout.addLayout(path_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "选择数据文件位置", self._edit.text(), "JSON Files (*.json)"
        )
        if path:
            self._edit.setText(path)

    def _restore_default(self):
        self._edit.setText(os.path.join(get_app_dir(), DEFAULT_DATA_FILENAME))

    def selected_path(self) -> str:
        return self._edit.text().strip()
```

- [ ] **Step 3: 提交**

```bash
git add app/ui/dialogs/
git commit -m "feat: add class management and settings dialogs"
```

---

## Task 10: 主窗口

**Files:**
- Create: `app/ui/main_window.py`

- [ ] **Step 1: 实现 `app/ui/main_window.py`**

```python
from __future__ import annotations
import uuid

from PyQt5.QtWidgets import (
    QAction, QComboBox, QHBoxLayout, QMainWindow, QMessageBox,
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
from app.ui.tab_stats import StatsTab
from app.ui.tab_students import StudentsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("随机点名系统")
        self.setMinimumSize(1000, 680)

        self._repo = Repository()
        self._data = self._repo.load()

        self._init_toolbar()
        self._init_tabs()
        self._refresh_class_combo()

    # ── Toolbar ──────────────────────────────────────────────────────────

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

    # ── Tabs ─────────────────────────────────────────────────────────────

    def _init_tabs(self):
        self._tab_widget = QTabWidget()
        self.setCentralWidget(self._tab_widget)

        current = self._current_class()
        self._roll_call_tab = RollCallTab(current, self._repo)
        self._students_tab = StudentsTab(current, self._repo)
        self._records_tab = RecordsTab(current, self._repo)
        self._stats_tab = StatsTab(current)

        self._tab_widget.addTab(self._roll_call_tab, "随机点名")
        self._tab_widget.addTab(self._students_tab, "学生管理")
        self._tab_widget.addTab(self._records_tab, "记录查询")
        self._tab_widget.addTab(self._stats_tab, "统计图表")

    def _current_class(self) -> ClassData:
        idx = self._class_combo.currentIndex()
        if idx >= 0 and idx < len(self._data.classes):
            return self._data.classes[idx]
        if self._data.classes:
            return self._data.classes[0]
        # 无班级时创建默认班级
        default = ClassData(id=str(uuid.uuid4()), name="默认班级")
        self._data.classes.append(default)
        self._repo.save()
        return default

    def _refresh_class_combo(self):
        self._class_combo.blockSignals(True)
        self._class_combo.clear()
        for c in self._data.classes:
            self._class_combo.addItem(c.name)
        self._class_combo.blockSignals(False)
        self._on_class_changed(self._class_combo.currentIndex())

    def _on_class_changed(self, index: int):
        if index < 0 or index >= len(self._data.classes):
            return
        cls = self._data.classes[index]
        self._roll_call_tab.set_class_data(cls)
        self._students_tab.set_class_data(cls)
        self._records_tab.set_class_data(cls)
        self._stats_tab.set_class_data(cls)

    # ── Class CRUD ───────────────────────────────────────────────────────

    def _create_class(self):
        dlg = CreateClassDialog(self)
        if dlg.exec_() != CreateClassDialog.Accepted:
            return
        new_cls = ClassData(id=str(uuid.uuid4()), name=dlg.class_name())
        self._data.classes.append(new_cls)
        self._repo.save()
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
        cls.name = dlg.class_name()
        self._repo.save()
        self._class_combo.setItemText(idx, cls.name)

    def _delete_class(self):
        idx = self._class_combo.currentIndex()
        if idx < 0:
            return
        cls = self._data.classes[idx]
        dlg = DeleteClassDialog(cls.name, self)
        if dlg.exec_() != DeleteClassDialog.Accepted:
            return
        self._data.classes.pop(idx)
        self._repo.save()
        self._refresh_class_combo()

    # ── Settings ─────────────────────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self._repo.data_path, self)
        if dlg.exec_() != SettingsDialog.Accepted:
            return
        self._repo.set_data_path(dlg.selected_path())
```

- [ ] **Step 2: 提交**

```bash
git add app/ui/main_window.py
git commit -m "feat: add main window with class toolbar and tab container"
```

---

## Task 11: 随机点名 Tab

**Files:**
- Create: `app/ui/tab_roll_call.py`

- [ ] **Step 1: 实现 `app/ui/tab_roll_call.py`**

```python
from __future__ import annotations
import datetime

from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from app.data.models import ClassData, Record, Student
from app.data.repository import Repository
from app.logic.roll_call import RollCallEngine
from app.ui.widgets.animation_widget import AnimationWidget
from app.ui.widgets.status_panel import StatusPanel


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

    # ── UI Setup ─────────────────────────────────────────────────────────

    def _init_ui(self):
        root = QHBoxLayout(self)

        # 左侧：点名操作
        left = QVBoxLayout()
        self._animation = AnimationWidget()
        self._animation.animation_finished.connect(self._on_animation_done)
        left.addWidget(self._animation, stretch=3)

        btn_row = QHBoxLayout()
        self._random_btn = QPushButton("随机点名")
        self._random_btn.clicked.connect(self._random_roll)
        self._manual_btn = QPushButton("手动点名")
        self._manual_btn.clicked.connect(self._manual_roll)
        btn_row.addWidget(self._random_btn)
        btn_row.addWidget(self._manual_btn)
        left.addLayout(btn_row)

        self._student_list = QListWidget()
        self._student_list.setMaximumHeight(120)
        left.addWidget(QLabel("学生名单（手动点名用）："))
        left.addWidget(self._student_list)

        score_row = QHBoxLayout()
        score_row.addWidget(QLabel("评分（0-100）："))
        self._score_spin = QSpinBox()
        self._score_spin.setRange(0, 100)
        self._score_spin.setValue(60)
        score_row.addWidget(self._score_spin)
        score_row.addStretch()
        left.addLayout(score_row)

        self._save_btn = QPushButton("保存本次记录")
        self._save_btn.clicked.connect(self._save_record)
        self._reset_btn = QPushButton("重置轮询")
        self._reset_btn.clicked.connect(self._reset_called)
        left.addWidget(self._save_btn)
        left.addWidget(self._reset_btn)
        left.addStretch()

        root.addLayout(left, stretch=2)

        # 右侧：状态面板
        self._status_panel = StatusPanel()
        root.addWidget(self._status_panel, stretch=1)

    # ── Actions ──────────────────────────────────────────────────────────

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
        names = [s.name for s in self._class_data.students if s.status == "normal"]
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
        normal_students = [s for s in self._class_data.students if s.status == "normal"]
        if idx < len(normal_students):
            self._selected_student = normal_students[idx]
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

    # ── Refresh ──────────────────────────────────────────────────────────

    def _refresh(self):
        self._student_list.clear()
        for s in self._class_data.students:
            if s.status == "normal":
                self._student_list.addItem(f"{s.id}  {s.name}")
        self._status_panel.refresh(
            self._engine.get_called(),
            self._engine.get_uncalled(),
        )
```

- [ ] **Step 2: 提交**

```bash
git add app/ui/tab_roll_call.py
git commit -m "feat: add roll call tab with animation and status panel"
```

---

## Task 12: 学生管理 Tab

**Files:**
- Create: `app/ui/tab_students.py`

- [ ] **Step 1: 实现 `app/ui/tab_students.py`**

```python
from __future__ import annotations

import openpyxl
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QInputDialog,
    QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from app.data.models import ClassData, Student
from app.data.repository import Repository

_STATUS_OPTIONS = ["正常", "缺席", "请假"]
_STATUS_MAP = {"normal": "正常", "absent": "缺席", "leave": "请假"}
_STATUS_RMAP = {"正常": "normal", "缺席": "absent", "请假": "leave"}


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

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["学号", "姓名", "状态"])
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
            combo = QComboBox()
            combo.addItems(_STATUS_OPTIONS)
            combo.setCurrentText(_STATUS_MAP.get(s.status, "正常"))
            combo.currentTextChanged.connect(
                lambda text, sid=s.id: self._on_status_changed(sid, text)
            )
            self._table.setCellWidget(row, 2, combo)

    def _on_status_changed(self, student_id: str, text: str):
        for s in self._class_data.students:
            if s.id == student_id:
                s.status = _STATUS_RMAP.get(text, "normal")
                break
        self._repo.save()

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
```

- [ ] **Step 2: 提交**

```bash
git add app/ui/tab_students.py
git commit -m "feat: add students tab with Excel import and status management"
```

---

## Task 13: 记录查询 Tab

**Files:**
- Create: `app/ui/tab_records.py`

- [ ] **Step 1: 实现 `app/ui/tab_records.py`**

```python
from __future__ import annotations
import datetime

import openpyxl
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget,
)

from app.data.models import ClassData
from app.data.repository import Repository
from app.logic.statistics import calc_class_stats

_STATUS_LABEL = {"normal": "正常", "absent": "缺席", "leave": "请假"}


class RecordsTab(QWidget):
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

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["学号", "姓名", "时间", "分数", "状态"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        del_btn = QPushButton("删除选中记录")
        del_btn.clicked.connect(self._delete_record)
        export_btn = QPushButton("导出本班成绩单")
        export_btn.clicked.connect(self._export_single)
        export_all_btn = QPushButton("导出全部班级")
        export_all_btn.clicked.connect(self._export_all)
        for btn in (del_btn, export_btn, export_all_btn):
            btn_row.addWidget(btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addWidget(QLabel("统计（点名次数 / 平均分）："))
        self._stat_text = QTextEdit()
        self._stat_text.setReadOnly(True)
        self._stat_text.setMaximumHeight(150)
        layout.addWidget(self._stat_text)

    def _refresh(self):
        self._table.setRowCount(0)
        for r in self._class_data.records:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(r.student_id))
            self._table.setItem(row, 1, QTableWidgetItem(r.name))
            self._table.setItem(row, 2, QTableWidgetItem(r.time))
            self._table.setItem(row, 3, QTableWidgetItem(str(r.score)))
            self._table.setItem(row, 4, QTableWidgetItem(_STATUS_LABEL.get(r.status, r.status)))
        self._refresh_stats()

    def _refresh_stats(self):
        stats = calc_class_stats(self._class_data.records)
        lines = [f"【{self._class_data.name}】统计\n姓名\t\t次数\t均分\n" + "-" * 40]
        for s in stats:
            lines.append(f"{s['name']}\t\t{s['count']} 次\t{s['avg_score']} 分")
        self._stat_text.setText("\n".join(lines))

    def _delete_record(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一条记录。")
            return
        del self._class_data.records[row]
        self._repo.save()
        self._refresh()

    def _export_single(self):
        default_name = f"{self._class_data.name}成绩单_{datetime.date.today()}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "导出成绩单", default_name, "Excel Files (*.xlsx)")
        if not path:
            return
        wb = openpyxl.Workbook()
        self._write_class_sheet(wb.active, self._class_data.name, self._class_data.records)
        wb.save(path)
        QMessageBox.information(self, "成功", "成绩单已导出。")

    def _export_all(self):
        default_name = f"全部班级成绩单_{datetime.date.today()}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "导出全部班级", default_name, "Excel Files (*.xlsx)")
        if not path:
            return
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        all_classes = self._repo.data.classes if self._repo.data else []
        for cls in all_classes:
            ws = wb.create_sheet(title=cls.name[:31])
            self._write_class_sheet(ws, cls.name, cls.records)
        wb.save(path)
        QMessageBox.information(self, "成功", "全部班级成绩单已导出。")

    @staticmethod
    def _write_class_sheet(ws, class_name: str, records) -> None:
        ws.title = class_name[:31]
        ws.append(["学号", "姓名", "点名次数", "平均分"])
        stats = calc_class_stats(records)
        for s in stats:
            ws.append([s["student_id"], s["name"], s["count"], s["avg_score"]])
```

- [ ] **Step 2: 提交**

```bash
git add app/ui/tab_records.py
git commit -m "feat: add records tab with stats and single/all-class export"
```

---

## Task 14: 统计图表 Tab

**Files:**
- Create: `app/ui/tab_stats.py`

- [ ] **Step 1: 实现 `app/ui/tab_stats.py`**

```python
from __future__ import annotations

# matplotlib 后端和字体必须在 main.py 中 matplotlib.use("Agg") 之后才导入本模块
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False

from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
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
```

- [ ] **Step 2: 提交**

```bash
git add app/ui/tab_stats.py
git commit -m "feat: add stats tab with matplotlib bar chart"
```

---

## Task 15: 入口 + 主题 + 中文字体

**Files:**
- Create: `main.py`

- [ ] **Step 1: 实现 `main.py`**

```python
import sys
import matplotlib
matplotlib.use("Agg")

from PyQt5.QtWidgets import QApplication
import qdarktheme

from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(qdarktheme.load_stylesheet("light"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 启动程序，手动验证以下场景**

```bash
python main.py
```

验证清单：
- [ ] 程序正常启动，无报错
- [ ] 主题为浅色现代风格
- [ ] 工具栏显示班级下拉 + 操作按钮
- [ ] 四个 Tab 均可正常切换
- [ ] 新建班级 → 班级出现在下拉框
- [ ] 导入 `assets/` 下的 xlsx 名单 → 16 名学生正确显示（无表头行）
- [ ] 随机点名 → 动画约 1.5s 后定格
- [ ] 全部点完后提示是否重置
- [ ] 保存记录 → 记录查询 Tab 显示记录
- [ ] 统计图表 Tab 显示柱状图
- [ ] 删除班级时需输入班级名确认

- [ ] **Step 3: 提交**

```bash
git add main.py app/ui/tab_stats.py
git commit -m "feat: wire up entry point with light theme and matplotlib Chinese font fix"
```

---

## Task 16: 向下兼容验证

**Files:** 无新文件，验证任务

- [ ] **Step 1: 复制旧格式文件并启动**

```bash
cp tests/fixtures/v1_data.json roll_call_data.json
python main.py
```

验证：
- [ ] 程序正常启动
- [ ] 自动迁移，`roll_call_data.json` 变为 v2 格式（`"version": 2`）
- [ ] 生成备份文件 `roll_call_data.v1.bak.json`
- [ ] 所有班级、学生、历史记录均正确展示

- [ ] **Step 2: 运行全套单元测试**

```bash
pytest tests/ -v
```

预期：全部 PASS。

- [ ] **Step 3: 清理测试数据**

```bash
rm -f roll_call_data.json roll_call_data.v1.bak.json
```

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "chore: final verification and cleanup"
```

---

## 附：已修复 Bug 对应任务

| Bug | 修复位置 |
|-----|----------|
| B1 `init_data` 自引用崩溃 | Task 2（models 替代原始结构） |
| B2 `QLineEdit.getText` 不存在 | Task 12（改用 `QInputDialog`） |
| B3 `manage_student_list` 不刷新 | Task 12（重写 students tab） |
| B4 无班级切换机制 | Task 10（QComboBox + `set_class_data`） |
| B5 Excel 导入未跳表头 | Task 12（`min_row=2`） |
| B6 统计按姓名聚合 | Task 6（按 `student_id` 聚合） |
| B7 `DATA_PATH` 相对路径 | Task 4（`get_app_dir()`） |
| B8 `import random` 在函数内 | Task 5（顶部 import） |
