import pytest
from app.data.models import Record
from app.logic.statistics import calc_class_stats


@pytest.fixture
def records():
    return [
        Record(student_id="001", name="张三", time="2026-05-01 09:00:00", score=80),
        Record(student_id="001", name="张三", time="2026-05-02 09:00:00", score=90),
        Record(student_id="002", name="李四", time="2026-05-01 09:00:00", score=70),
        Record(student_id="003", name="张三", time="2026-05-01 09:00:00", score=60),
        # id=003 的学生姓名也是"张三"，旧版会合并，新版按 student_id 区分
    ]


def test_calc_counts(records):
    stats = calc_class_stats(records)
    entry_001 = next(s for s in stats if s["student_id"] == "001")
    assert entry_001["count"] == 2


def test_calc_avg_score(records):
    stats = calc_class_stats(records)
    entry_001 = next(s for s in stats if s["student_id"] == "001")
    assert entry_001["avg_score"] == 85.0


def test_different_ids_same_name_not_merged(records):
    stats = calc_class_stats(records)
    zhang_entries = [s for s in stats if s["name"] == "张三"]
    assert len(zhang_entries) == 2  # 001 和 003 分开统计


def test_empty_records():
    assert calc_class_stats([]) == []


def test_result_sorted_by_name(records):
    stats = calc_class_stats(records)
    names = [s["name"] for s in stats]
    assert names == sorted(names)
