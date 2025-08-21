import logging
import threading
import tkinter as tk
from tkinter import scrolledtext

from .auth import AuthClient
from .api import ESDAPI
from .excel_writer import ExcelWriter
from .state import State
from .poller import Poller
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


def launch_gui():
    cfg = yaml.safe_load(open("config.yaml"))
    auth = AuthClient(cfg["app"].get("base_url", "https://esdguruapi.eschooldata.com"),
                      cfg["api"]["token_endpoint"], "openid profile offline_access")
    api = ESDAPI(cfg["app"].get("base_url", "https://esdguruapi.eschooldata.com"), cfg, auth)
    excel_writer = ExcelWriter(cfg)
    state = State(Path("data/state.json"))

    root = tk.Tk()
    root.title("eSchool Tardy Recorder")

    log_box = scrolledtext.ScrolledText(root, width=80, height=20, state="disabled")
    log_box.pack(padx=10, pady=10)

    stop_event = threading.Event()
    poller = None

    def start():
        nonlocal poller
        stop_event.clear()
        poller = Poller(api, excel_writer, state, cfg, stop_event)
        poller.start()
        logger.info("Started polling")

    def stop():
        stop_event.set()
        logger.info("Stopping poller...")

    start_btn = tk.Button(root, text="Start", command=start)
    start_btn.pack(side="left", padx=5)

    stop_btn = tk.Button(root, text="Stop", command=stop)
    stop_btn.pack(side="left", padx=5)

    def log_writer(record):
        msg = f"{record.levelname} | {record.getMessage()}\n"
        log_box.configure(state="normal")
        log_box.insert("end", msg)
        log_box.configure(state="disabled")
        log_box.see("end")

    class TextHandler(logging.Handler):
        def emit(self, record):
            log_writer(record)

    logging.getLogger().addHandler(TextHandler())

    root.mainloop()
