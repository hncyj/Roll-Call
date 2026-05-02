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
