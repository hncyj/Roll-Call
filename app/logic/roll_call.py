from __future__ import annotations
import random
from typing import List, Optional

from app.data.models import ClassData, Student


class RollCallEngine:
    def __init__(self, class_data: ClassData):
        self._class_data = class_data

    def get_uncalled(self) -> List[Student]:
        called_set = set(self._class_data.called_ids)
        return [s for s in self._class_data.students if s.id not in called_set]

    def get_called(self) -> List[Student]:
        called_set = set(self._class_data.called_ids)
        return [s for s in self._class_data.students if s.id in called_set]

    def pick_random(self) -> Optional[Student]:
        uncalled = self.get_uncalled()
        if not uncalled:
            return None
        return random.choice(uncalled)

    def mark_called(self, student_id: str) -> None:
        if student_id not in self._class_data.called_ids:
            self._class_data.called_ids.append(student_id)

    def reset(self) -> None:
        self._class_data.called_ids.clear()

    def is_complete(self) -> bool:
        return len(self.get_uncalled()) == 0
