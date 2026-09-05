import pytest
from app.data.models import Student, Record, ClassData, AppData


def test_student_fields():
    s = Student(id="001", name="张三")
    assert s.to_dict() == {"id": "001", "name": "张三"}


def test_student_round_trip():
    s = Student(id="001", name="张三")
    assert Student.from_dict(s.to_dict()) == s


def test_student_from_dict_coerces_int_id():
    s = Student.from_dict({"id": 2541123101, "name": "曾璟宁"})
    assert s.id == "2541123101"
    assert s.name == "曾璟宁"


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
