import json
from pathlib import Path
from typing import Optional


class State:
    def __init__(self, path: Path):
        self.path = path
        self.data = {"last_event_id": None, "last_timestamp": None}
        if path.exists():
            try:
                self.data.update(json.loads(path.read_text()))
            except Exception:
                pass

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2))

    def update_event(self, event_id: str, ts_iso: str):
        self.data["last_event_id"] = event_id
        self.data["last_timestamp"] = ts_iso
        self.save()

    def last(self) -> Optional[str]:
        return self.data.get("last_timestamp")
