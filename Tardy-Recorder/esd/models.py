from dataclasses import dataclass
from datetime import datetime
from typing import Optional



@dataclass
class Student:
    id: str
    name: str
    grade: Optional[str] = None



@dataclass
class TardyEvent:
    event_id: str # unique id from API if available; else compose from ts+id
    student_id: str
    occurred_at: datetime
    # raw payload is kept for auditing (optional)
    raw: dict