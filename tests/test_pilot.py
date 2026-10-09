"""Tests for pilot study logging and the /pilot endpoints."""
import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.pilot_logger import log_event

client = TestClient(app)


def test_stats_empty():
    r = client.get("/api/v1/pilot/stats")
    assert r.status_code == 200
    assert r.json()["total_events"] == 0


def test_export_missing_log_returns_404():
    assert client.get("/api/v1/pilot/export").status_code == 404


def test_log_event_writes_jsonl(isolated_pilot_log):
    log_event("assess_vl", {"teacher_id": "t1", "vl_level": "beginner"})
    lines = isolated_pilot_log.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[0])
    assert record["event"] == "assess_vl"
    assert record["teacher_id"] == "t1"
    assert "ts" in record


def test_stats_aggregation():
    log_event("assess_vl", {"teacher_id": "t1", "vl_level": "beginner"})
    log_event("assess_vl", {"teacher_id": "t2", "vl_level": "advanced"})
    log_event("report", {"teacher_id": "t1", "score": 0.6})
    log_event("report", {"teacher_id": "t2", "score": 0.8})
    log_event("scaffold", {"teacher_id": "t1", "current_step": "data_exploration"})

    data = client.get("/api/v1/pilot/stats").json()
    assert data["total_events"] == 5
    assert data["unique_teachers"] == 2
    assert data["vl_level_distribution"] == {"beginner": 1, "advanced": 1}
    assert data["report_scores"]["mean"] == 0.7
    assert data["scaffold_requests_by_step"] == {"data_exploration": 1}


def test_export_returns_raw_jsonl():
    log_event("chat", {"teacher_id": "t1"})
    r = client.get("/api/v1/pilot/export")
    assert r.status_code == 200
    assert json.loads(r.text.strip())["event"] == "chat"


def test_corrupt_lines_are_skipped(isolated_pilot_log):
    log_event("chat", {"teacher_id": "t1"})
    with isolated_pilot_log.open("a", encoding="utf-8") as f:
        f.write("not json\n")
    assert client.get("/api/v1/pilot/stats").json()["total_events"] == 1
