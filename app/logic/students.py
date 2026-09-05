from app.data.models import ClassData, Student


def validate_students(students: list[Student]) -> None:
    if len(students) > 200:
        raise ValueError("学生人数不能超过 200 人。")
    seen = set()
    for student in students:
        if not student.id.strip() or not student.name.strip():
            raise ValueError("学号和姓名不能为空。")
        if student.id in seen:
            raise ValueError(f"学号重复：{student.id}。每个学生必须使用唯一学号。")
        seen.add(student.id)


def edit_student(class_data: ClassData, student: Student, sid: str, name: str) -> None:
    replacement = Student(sid.strip(), name.strip())
    validate_students([replacement if s is student else s for s in class_data.students])
    old_id = student.id
    if replacement.id != old_id and (
        replacement.id in class_data.called_ids
        or any(r.student_id == replacement.id for r in class_data.records)
    ):
        raise ValueError("该学号已有历史记录或本轮点名状态，不能合并为另一名学生。")
    for record in class_data.records:
        if record.student_id == old_id:
            record.student_id = replacement.id
    class_data.called_ids = [replacement.id if sid == old_id else sid for sid in class_data.called_ids]
    student.id = replacement.id
    student.name = replacement.name
