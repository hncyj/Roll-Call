import pytest
from app.data.models import ClassData, Student
from app.logic.roll_call import RollCallEngine


@pytest.fixture
def class_with_students():
    c = ClassData(id="cls_001", name="工商管理班")
    c.students = [
        Student(id="001", name="张三"),
        Student(id="002", name="李四"),
        Student(id="003", name="王五"),
        Student(id="004", name="赵六"),
    ]
    return c


def test_get_uncalled_includes_entire_roster(class_with_students):
    engine = RollCallEngine(class_with_students)
    uncalled = engine.get_uncalled()
    ids = [s.id for s in uncalled]
    assert "001" in ids
    assert "002" in ids
    assert "003" in ids
    assert "004" in ids


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
    assert student.id in ["001", "002", "003", "004"]


def test_pick_random_returns_none_when_complete(class_with_students):
    class_with_students.called_ids = ["001", "002", "003", "004"]
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
    class_with_students.called_ids = ["001", "002", "003", "004"]
    engine = RollCallEngine(class_with_students)
    assert engine.is_complete() is True


def test_reset_does_not_change_roster(class_with_students):
    class_with_students.called_ids = ["001"]
    engine = RollCallEngine(class_with_students)
    engine.reset()
    assert len(class_with_students.students) == 4
    assert class_with_students.students[2].name == "王五"


def test_entire_round_has_no_duplicates(class_with_students):
    engine = RollCallEngine(class_with_students)
    picked = []
    for _ in range(4):
        student = engine.pick_random()
        picked.append(student.id)
        engine.mark_called(student.id)
    assert len(set(picked)) == 4
    assert engine.pick_random() is None
