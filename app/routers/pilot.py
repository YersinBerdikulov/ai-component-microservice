"""
GET /api/v1/pilot/stats  — aggregate pilot study metrics for dissertation analysis.
GET /api/v1/pilot/export — raw JSONL events for pandas import.
"""
import json
import os
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter()

LOG_PATH = Path(os.getenv("PILOT_LOG_PATH", "logs/pilot_events.jsonl"))


def _read_events() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    events = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


@router.get("/pilot/stats")
async def pilot_stats():
    events = _read_events()
    if not events:
        return {"total_events": 0, "message": "No pilot data recorded yet"}

    teachers = set()
    by_event = defaultdict(int)
    vl_distribution = defaultdict(int)
    scores = []
    scaffold_steps = defaultdict(int)

    for e in events:
        by_event[e["event"]] += 1
        if "teacher_id" in e:
            teachers.add(e["teacher_id"])
        if e["event"] == "assess_vl" and "vl_level" in e:
            vl_distribution[e["vl_level"]] += 1
        if e["event"] == "report" and "score" in e:
            scores.append(e["score"])
        if e["event"] == "scaffold" and "current_step" in e:
            scaffold_steps[e["current_step"]] += 1

    return {
        "total_events": len(events),
        "unique_teachers": len(teachers),
        "events_by_type": dict(by_event),
        "vl_level_distribution": dict(vl_distribution),
        "report_scores": {
            "count": len(scores),
            "mean": round(sum(scores) / len(scores), 3) if scores else None,
            "min": min(scores) if scores else None,
            "max": max(scores) if scores else None,
        },
        "scaffold_requests_by_step": dict(scaffold_steps),
    }


@router.get("/pilot/export", response_class=PlainTextResponse)
async def pilot_export():
    """Returns raw JSONL — load directly with pandas: pd.read_json('...', lines=True)"""
    if not LOG_PATH.exists():
        raise HTTPException(status_code=404, detail="No pilot log file found")
    return LOG_PATH.read_text(encoding="utf-8")
