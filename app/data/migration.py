from __future__ import annotations
from typing import Any, Dict


def is_v1(raw: Dict[str, Any]) -> bool:
    return "version" not in raw


def migrate_v1_to_v2(raw: Dict[str, Any]) -> Dict[str, Any]:
    class_names = raw.get("classes", [])
    students_map = raw.get("students", {})
    records_map = raw.get("records", {})

    classes = []
    for i, name in enumerate(class_names):
        students = [
            {"id": str(s["id"]), "name": s["name"]}
            for s in students_map.get(name, [])
            if str(s.get("id", "")) != "学号"  # 跳过 Excel 导入时残留的表头行
        ]
        records = [
            {
                "student_id": str(r.get("id", r.get("student_id", ""))),
                "name": r["name"],
                "time": r["time"],
                "score": r["score"],
            }
            for r in records_map.get(name, [])
        ]
        classes.append({
            "id": f"cls_{i:03d}",
            "name": name,
            "students": students,
            "records": records,
            "called_ids": [],  # 旧格式 called_students 存姓名非 ID，迁移时重置轮次
        })

    return {"version": 2, "classes": classes, "settings": {}}
