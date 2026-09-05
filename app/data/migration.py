from __future__ import annotations
from typing import Any, Dict


def is_v1(raw: Dict[str, Any]) -> bool:
    return isinstance(raw, dict) and "version" not in raw and isinstance(raw.get("classes"), list) and isinstance(raw.get("students"), dict)


def migrate_v1_to_v2(raw: Dict[str, Any]) -> Dict[str, Any]:
    class_names = raw.get("classes", [])
    students_map = raw.get("students", {})
    records_map = raw.get("records", {})
    called_map = raw.get("called_students", {})

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
        called_ids = []
        valid_ids = {s["id"] for s in students}
        for entry in called_map.get(name, []):
            if isinstance(entry, dict):
                matches = [str(entry.get("id", entry.get("student_id", "")))]
            else:
                # 姓名格式存在同名歧义时保留所有匹配，避免迁移后重复抽取。
                value = str(entry)
                matches = [value] if value in valid_ids else [s["id"] for s in students if s["name"] == value]
            for sid in matches:
                if sid in valid_ids and sid not in called_ids:
                    called_ids.append(sid)
        classes.append({
            "id": f"cls_{i:03d}",
            "name": name,
            "students": students,
            "records": records,
            "called_ids": called_ids,
        })

    return {"version": 2, "classes": classes, "settings": {}}
