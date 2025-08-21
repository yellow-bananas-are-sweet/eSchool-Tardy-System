import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlencode

import requests

from .auth import AuthClient
from .models import Student, TardyEvent

logger = logging.getLogger(__name__)


class ESDAPI:
    def __init__(self, base_url: str, cfg: dict, auth: AuthClient):
        self.base_url = base_url.rstrip("/")
        self.cfg = cfg
        self.auth = auth

    def _url(self, path: str) -> str:
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def fetch_attendance_since(self, since_iso: Optional[str]) -> List[dict]:
        path = self.cfg["api"]["attendance_path"]
        param = self.cfg["api"].get("attendance_since_param", "since")
        params = {param: since_iso} if since_iso else {}
        url = self._url(path)
        logger.debug("GET %s?%s", url, urlencode(params))
        r = requests.get(url, headers=self.auth.auth_header(), params=params, timeout=20)
        r.raise_for_status()
        return r.json() if r.content else []

    def get_student(self, student_id: str) -> Student:
        path = self.cfg["api"]["student_by_id_path"].format(id=student_id)
        url = self._url(path)
        r = requests.get(url, headers=self.auth.auth_header(), timeout=15)
        r.raise_for_status()
        data = r.json()
        name = f"{data.get('firstName','').strip()} {data.get('lastName','').strip()}".strip() or data.get("name", "")
        return Student(id=str(data.get("id", student_id)), name=name)

    def get_grade(self, student_id: str) -> Optional[str]:
        path = self.cfg["api"]["student_enrollments_path"].format(id=student_id)
        url = self._url(path)
        r = requests.get(url, headers=self.auth.auth_header(), timeout=15)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        payload = r.json() or []
        # naive selection; adjust for your schema
        best = payload[0] if payload else None
        return best.get("grade") if best else None

    def map_attendance_to_tardy(self, row: dict) -> Optional[TardyEvent]:
        # Adapt mapping to your payload
        if str(row.get("type", "")).lower() not in {"tardy", "late", "tardy_in"}:
            return None
        ts = row.get("timestamp") or row.get("occurredAt") or row.get("dateTime")
        if not ts:
            return None
        try:
            occurred_at = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
        sid = str(row.get("studentId") or row.get("student", {}).get("id"))
        if not sid:
            return None
        eid = str(row.get("eventId") or f"{sid}-{int(occurred_at.timestamp())}")
        return TardyEvent(event_id=eid, student_id=sid, occurred_at=occurred_at, raw=row)
