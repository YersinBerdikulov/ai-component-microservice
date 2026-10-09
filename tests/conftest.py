"""Shared fixtures."""
import pytest

from app.routers import pilot
from app.services import pilot_logger


@pytest.fixture(autouse=True)
def isolated_pilot_log(tmp_path, monkeypatch):
    """Keep test events out of the real pilot study log."""
    log_path = tmp_path / "pilot_events.jsonl"
    monkeypatch.setattr(pilot_logger, "LOG_PATH", log_path)
    monkeypatch.setattr(pilot, "LOG_PATH", log_path)
    return log_path
