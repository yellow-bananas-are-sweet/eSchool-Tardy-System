
PROJECT STRUCTURE

eschool-tardy-recorder/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ config.yaml
├─ app.py                  # Entry point
├─ esd/
│  ├─ __init__.py
│  ├─ logging_config.py    # Standard logging setup (console + rotating file)
│  ├─ auth.py              # OAuth2 client + token refresh
│  ├─ api.py               # REST calls to eSD endpoints
│  ├─ models.py            # Dataclasses for Student, TardyEvent
│  ├─ excel_writer.py      # Weekly Excel writer (single sheet)
│  ├─ state.py             # Local checkpoint: last seen event id/timestamp
│  ├─ utils.py             # Time/date helpers (week keys, business days)
│  ├─ poller.py            # Background polling worker (every 5s)
│  └─ gui.py               # Tkinter GUI (start/stop + live log)
└─ data/
   ├─ logs/                # Rotating log files
   └─ output/              # Weekly Excel output files