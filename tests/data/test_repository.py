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


def test_custom_path_and_round_survive_restart(tmp_path):
    repo = Repository()
    data = repo.load()
    data.classes.append(ClassData("a", "A", [Student("001", "Alice")]))
    repo.save()
    custom_path = str(tmp_path / "external" / "custom.json")
    repo.set_data_path(custom_path)
    data.classes[0].called_ids.append("001")
    repo.save()
    restarted = Repository()
    assert restarted.data_path == custom_path
    assert restarted.load().classes[0].called_ids == ["001"]


def test_missing_configured_file_does_not_create_empty_data(tmp_path):
    repo = Repository()
    repo.load()
    path = tmp_path / "external" / "data.json"
    repo.set_data_path(str(path))
    path.unlink()
    with pytest.raises(FileNotFoundError):
        Repository().load()
    assert not path.exists()


def test_existing_target_is_loaded_not_overwritten(tmp_repo, tmp_path):
    original = tmp_repo.load()
    original.classes.append(ClassData("a", "A"))
    other = tmp_path / "other.json"
    other.write_text(json.dumps(AppData(classes=[ClassData("b", "B")]).to_dict()))
    before = other.read_bytes()
    tmp_repo.set_data_path(str(other))
    assert tmp_repo.data.classes[0].id == "b"
    assert other.read_bytes() == before


def test_failed_path_setting_keeps_previous_path_and_restart(tmp_repo, tmp_path, monkeypatch):
    tmp_repo.load()
    original_path = tmp_repo.data_path
    original_write = tmp_repo._write_json
    def fail_settings(path, data):
        if path.endswith("rollcall_settings.json"):
            raise OSError("disk full")
        original_write(path, data)
    monkeypatch.setattr(tmp_repo, "_write_json", fail_settings)
    with pytest.raises(OSError):
        tmp_repo.set_data_path(str(tmp_path / "new.json"))
    assert tmp_repo.data_path == original_path
    assert not (tmp_path / "rollcall_settings.json").exists()


def test_invalid_existing_target_does_not_switch(tmp_repo, tmp_path):
    tmp_repo.load()
    previous = tmp_repo.data_path
    path = tmp_path / "unrelated.json"
    path.write_text('{"data_path": "x"}')
    with pytest.raises(ValueError):
        tmp_repo.set_data_path(str(path))
    assert tmp_repo.data_path == previous


def test_failed_save_restores_class_state(tmp_repo, monkeypatch):
    data = tmp_repo.load()
    cls = ClassData("a", "A")
    data.classes.append(cls)
    def fail():
        raise OSError("disk full")
    monkeypatch.setattr(tmp_repo, "save", fail)
    with pytest.raises(OSError):
        with tmp_repo.edit_class(cls):
            cls.called_ids.append("001")
    assert cls.called_ids == []
    assert data.classes[0] is cls


def test_migration_written_once_and_backup_preserved(v1_repo):
    before = open(v1_repo.data_path, "rb").read()
    v1_repo.load()
    with open(v1_repo.data_path, encoding="utf-8") as f:
        assert json.load(f)["version"] == 2
    backup = v1_repo.data_path.replace(".json", ".v1.bak.json")
    assert open(backup, "rb").read() == before
    v1_repo.load()
    assert open(backup, "rb").read() == before


def test_failed_atomic_replace_keeps_original_file(tmp_repo, monkeypatch):
    data = tmp_repo.load()
    data.classes.append(ClassData("a", "A"))
    tmp_repo.save()
    with open(tmp_repo.data_path, "rb") as f:
        before = f.read()
    def fail(*args):
        raise OSError("replace failed")
    monkeypatch.setattr("app.data.repository.os.replace", fail)
    with pytest.raises(OSError):
        with tmp_repo.edit_class(data.classes[0]):
            data.classes[0].called_ids.append("001")
    with open(tmp_repo.data_path, "rb") as f:
        assert f.read() == before
    assert data.classes[0].called_ids == []
    assert not os.path.exists(tmp_repo.data_path + ".tmp")


@pytest.mark.parametrize("raw", [[], None, {"version": 3, "classes": []}])
def test_reject_invalid_data_without_overwrite(tmp_repo, raw):
    with open(tmp_repo.data_path, "w", encoding="utf-8") as f:
        json.dump(raw, f)
    with pytest.raises(ValueError):
        tmp_repo.load()
    with open(tmp_repo.data_path, encoding="utf-8") as f:
        assert json.load(f) == raw
