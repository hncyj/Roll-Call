from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class Student:
    id: str
    name: str

    @classmethod
    def from_dict(cls, d: dict) -> Student:
        return cls(id=str(d["id"]), name=d["name"])

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


@dataclass
class Record:
    student_id: str
    name: str
    time: str
    score: int

    @classmethod
    def from_dict(cls, d: dict) -> Record:
        return cls(
            student_id=str(d.get("student_id", d.get("id", ""))),
            name=d["name"],
            time=d["time"],
            score=int(d["score"]),
        )

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "time": self.time,
            "score": self.score,
        }


@dataclass
class ClassData:
    id: str
    name: str
    students: List[Student] = field(default_factory=list)
    records: List[Record] = field(default_factory=list)
    called_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> ClassData:
        return cls(
            id=d["id"],
            name=d["name"],
            students=[Student.from_dict(s) for s in d.get("students", [])],
            records=[Record.from_dict(r) for r in d.get("records", [])],
            called_ids=[str(i) for i in d.get("called_ids", [])],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "students": [s.to_dict() for s in self.students],
            "records": [r.to_dict() for r in self.records],
            "called_ids": self.called_ids,
        }


@dataclass
class AppData:
    version: int = 2
    classes: List[ClassData] = field(default_factory=list)
    settings: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> AppData:
        return cls(
            version=d.get("version", 2),
            classes=[ClassData.from_dict(c) for c in d.get("classes", [])],
            settings=d.get("settings", {}),
        )

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "classes": [c.to_dict() for c in self.classes],
            "settings": self.settings,
        }
