import logging
import threading
import time
from datetime import datetime

from .utils import is_weekday

logger = logging.getLogger(__name__)


class Poller(threading.Thread):
    def __init__(self, api, excel_writer, state, cfg: dict, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.api = api
        self.excel_writer = excel_writer
        self.state = state
        self.cfg = cfg
        self.stop_event = stop_event

    def run(self):
        logger.info("Poller started")
        while not self.stop_event.is_set():
            try:
                if self.cfg["app"].get("weekday_only", True) and not is_weekday(datetime.now()):
                    logger.debug("Skipping weekend poll")
                else:
                    self.poll_once()
            except Exception as e:
                logger.exception("Error in poller: %s", e)
            time.sleep(self.cfg["app"].get("poll_interval_seconds", 5))
        logger.info("Poller stopped")

    def poll_once(self):
        since = self.state.last()
        rows = self.api.fetch_attendance_since(since)
        for row in rows:
            event = self.api.map_attendance_to_tardy(row)
            if not event:
                continue
            student = self.api.get_student(event.student_id)
            grade = self.api.get_grade(event.student_id)
            self.excel_writer.append(student, grade, event)
            self.state.update_event(event.event_id, event.occurred_at.isoformat())
