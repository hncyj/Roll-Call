import pytest

from app.data.models import ClassData, Student, Record
from app.logic.students import edit_student, validate_students
from app.logic.roll_call import RollCallEngine
from app.logic.statistics import calc_class_stats


@pytest.mark.parametrize("students", [
    [Student("1", "A"), Student("1", "B")],
    [Student(" ", "A")],
    [Student("1", " ")],
    [Student(str(i), "A") for i in range(201)],
])
def test_invalid_rosters_are_rejected(students):
    with pytest.raises(ValueError):
        validate_students(students)


def test_id_edit_keeps_history_and_round_linked():
    student = Student("001", "A")
    cls = ClassData("a", "A", [student], [Record("001", "A", "today", 80)], ["001"])
    edit_student(cls, student, "002", "Alice")
    assert cls.records[0].student_id == "002"
    assert cls.called_ids == ["002"]
    assert RollCallEngine(cls).get_uncalled() == []
    assert calc_class_stats(cls.records)[0]["avg_score"] == 80


def test_edit_cannot_merge_another_students_history():
    student = Student("001", "A")
    cls = ClassData("a", "A", [student], [Record("002", "B", "today", 80)])
    with pytest.raises(ValueError):
        edit_student(cls, student, "002", "A")
    assert student.id == "001"
