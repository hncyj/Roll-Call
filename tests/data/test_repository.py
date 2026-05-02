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
