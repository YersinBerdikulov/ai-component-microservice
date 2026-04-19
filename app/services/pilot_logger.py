"""
Writes one JSON-line per AI interaction to logs/pilot_events.jsonl.
Used during апробация to collect empirical data for analysis.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(os.getenv("PILOT_LOG_PATH", "logs/pilot_events.jsonl"))


def log_event(event_type: str, payload: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            **payload,
        }
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass
