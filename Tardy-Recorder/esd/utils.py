from pathlib import Path
from datetime import datetime


def ensure_dirs(*paths: Path):
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def is_weekday(dt: datetime) -> bool:
    return dt.weekday() < 5  # 0=Mon, ... 6=Sun


def week_key(dt: datetime) -> str:
    return f"{dt.isocalendar().week:02d}"  # ISO week number
