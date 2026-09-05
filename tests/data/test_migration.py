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
    assert cls["students"][0]["name"] == "曾璟宁"


def test_migrate_records(v1_raw):
    result = migrate_v1_to_v2(v1_raw)
    cls = next(c for c in result["classes"] if c["name"] == "工商管理班")
    assert len(cls["records"]) == 1
    r = cls["records"][0]
    assert r["student_id"] == "2541123101"
    assert r["score"] == 85
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


def test_migrate_legacy_names_and_ids_preserves_round(v1_raw):
    name = "工商管理班"
    v1_raw["called_students"][name] = ["曾璟宁", "2541123102", "不存在", "曾璟宁"]
    result = migrate_v1_to_v2(v1_raw)
    assert result["classes"][0]["called_ids"] == ["2541123101", "2541123102"]


def test_unrelated_json_is_not_legacy_data():
    assert not is_v1({"data_path": "somewhere.json"})
