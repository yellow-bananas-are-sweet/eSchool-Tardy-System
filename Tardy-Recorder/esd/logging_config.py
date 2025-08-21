import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import yaml
from appdirs import user_data_dir

APP_NAME = "eSchool Tardy Recorder"

def _load_yaml(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def setup_logging():
    # Load configuration and ensure log directory exists
    cfg = _load_yaml(Path("config.yaml"))
    logs_dir = Path(cfg.get("app", {}).get("logs_dir", "data/logs"))
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Define log format
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Rotating file handler
    fh = RotatingFileHandler(logs_dir / "tardy_recorder.log", maxBytes=2_000_000, backupCount=5)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Suppress verbose logs from urllib3
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info("Logging initialized")
