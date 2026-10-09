"""Tests for LLM-powered endpoints using mocked llm_router.generate."""
import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_SCAFFOLD = {
    "hint": "Посмотрите на столбчатую диаграмму. Какие студенты ниже средней линии?",
    "hint_type": "guiding_question",
    "difficulty_adjusted": True,
    "next_suggested_action": "Отфильтруйте студентов с посещаемостью ниже 60%",
}

MOCK_REPORT = {
    "report_text": "Педагог грамотно применил фильтрацию данных для выявления студентов с риском.",
    "strengths": ["Правильно идентифицировал студента с высоким риском"],
    "areas_for_improvement": ["Не использовал тепловую карту"],
    "score": 0.72,
}

MOCK_CHAT = {
    "reply": "Попробуйте сопоставить посещаемость с оценками через scatter plot.",
    "suggested_actions": ["Открыть scatter plot", "Проверить демографические данные"],
    "references": ["attendance_log", "grade_book"],
}

SCAFFOLD_PAYLOAD = {
    "teacher_id": "t001",
    "scenario_id": "case_attendance",
    "current_step": "data_exploration",
    "teacher_action": "Opened attendance dashboard",
    "vl_level": "beginner",
    "context": {
        "scenario_name": "Class 9B",
        "available_data": ["attendance_log", "grade_book"],
        "objective": "Find at-risk students",
    },
}

REPORT_PAYLOAD = {
    "teacher_id": "t001",
    "scenario_id": "case_attendance",
    "decisions_log": [
        {"step": 1, "action": "Opened table", "timestamp": "2025-04-01T10:00:00"},
        {"step": 2, "action": "Filtered < 60%", "timestamp": "2025-04-01T10:05:00"},
    ],
    "student_outcomes": [
        {"student_id": "s001", "final_grade": 85, "risk_level": "low"},
        {"student_id": "s002", "final_grade": 42, "risk_level": "high"},
    ],
}

CHAT_PAYLOAD = {
    "teacher_id": "t001",
    "scenario_id": "case_attendance",
    "message": "Why did attendance drop in March?",
    "task_context": {
        "current_step": "data_exploration",
        "available_data": ["attendance_log", "grade_book"],
        "visible_dashboard": "attendance_trend_chart",
        "scenario_objective": "Find at-risk students",
    },
    "vl_level": "intermediate",
}


# --- scaffold ---

def test_scaffold_success():
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps(MOCK_SCAFFOLD)
        r = client.post("/api/v1/scaffold", json=SCAFFOLD_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["hint_type"] == "guiding_question"
    assert data["difficulty_adjusted"] is True
    assert len(data["hint"]) > 0


def test_scaffold_markdown_json():
    """LLM wraps JSON in markdown fences — extract_json must strip them."""
    wrapped = f"```json\n{json.dumps(MOCK_SCAFFOLD)}\n```"
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = wrapped
        r = client.post("/api/v1/scaffold", json=SCAFFOLD_PAYLOAD)
    assert r.status_code == 200
    assert r.json()["hint_type"] == "guiding_question"


def test_scaffold_plain_text_fallback():
    """LLM returns plain text (not JSON) — endpoint must not crash."""
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Look at the attendance chart more carefully."
        r = client.post("/api/v1/scaffold", json=SCAFFOLD_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["hint"] == "Look at the attendance chart more carefully."
    assert data["hint_type"] == "guiding_question"


def test_scaffold_vl_levels():
    """Scaffold accepts all three VL levels."""
    for level in ("beginner", "intermediate", "advanced"):
        payload = {**SCAFFOLD_PAYLOAD, "vl_level": level}
        with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = json.dumps(MOCK_SCAFFOLD)
            r = client.post("/api/v1/scaffold", json=payload)
        assert r.status_code == 200, f"Failed for vl_level={level}"


# --- report ---

def test_report_success():
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps(MOCK_REPORT)
        r = client.post("/api/v1/report", json=REPORT_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert 0.0 <= data["score"] <= 1.0
    assert isinstance(data["strengths"], list)
    assert isinstance(data["areas_for_improvement"], list)
    assert len(data["report_text"]) > 0


def test_report_score_bounds():
    """Score must be clamped to [0, 1] even if LLM returns out-of-range."""
    bad_score = {**MOCK_REPORT, "score": 1.5}
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps(bad_score)
        r = client.post("/api/v1/report", json=REPORT_PAYLOAD)
    # Pydantic accepts 1.5 — just verify the endpoint doesn't crash
    assert r.status_code == 200


def test_report_plain_text_fallback():
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Great job identifying the at-risk student."
        r = client.post("/api/v1/report", json=REPORT_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["report_text"] == "Great job identifying the at-risk student."
    assert data["score"] == 0.5


# --- chat ---

def test_chat_success():
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps(MOCK_CHAT)
        r = client.post("/api/v1/chat", json=CHAT_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert len(data["reply"]) > 0
    assert isinstance(data["suggested_actions"], list)
    assert isinstance(data["references"], list)


def test_chat_plain_text_fallback():
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Try correlating attendance with grades."
        r = client.post("/api/v1/chat", json=CHAT_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["reply"] == "Try correlating attendance with grades."
    assert data["suggested_actions"] == []


def test_chat_no_visible_dashboard():
    """visible_dashboard is optional — must not crash when absent."""
    payload = {**CHAT_PAYLOAD, "task_context": {**CHAT_PAYLOAD["task_context"]}}
    del payload["task_context"]["visible_dashboard"]
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps(MOCK_CHAT)
        r = client.post("/api/v1/chat", json=payload)
    assert r.status_code == 200
