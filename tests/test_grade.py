"""Tests for the /grade endpoint using mocked llm_router.generate."""
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.grade import _label

client = TestClient(app)

GRADE_PAYLOAD = {
    "teacher_id": "t001",
    "task_id": "task_attendance_filter",
    "task_description": "Find students with attendance below 60%",
    "expected_approach": "Filter the DataFrame with df[df.attendance < 0.6]",
    "submitted_code": "df[df['attendance'] < 0.6]",
    "execution_result": {"output": "s002, s007", "error": None},
    "vl_level": "intermediate",
}


@pytest.mark.parametrize("score,label", [
    (0.95, "Отлично"),
    (0.85, "Отлично"),
    (0.75, "Хорошо"),
    (0.55, "Удовлетворительно"),
    (0.10, "Неудовлетворительно"),
])
def test_label_thresholds(score, label):
    assert _label(score) == label


def test_grade_success():
    llm_reply = {
        "score": 0.9,
        "grade_label": "Отлично",
        "is_correct": True,
        "feedback": "Верный фильтр.",
        "code_issues": [],
        "recommendations": ["Отсортируйте результат"],
    }
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps(llm_reply)
        r = client.post("/api/v1/grade", json=GRADE_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["score"] == 0.9
    assert data["is_correct"] is True
    assert data["recommendations"] == ["Отсортируйте результат"]


def test_grade_score_is_clamped_and_labelled():
    """Out-of-range score is clamped to [0, 1]; missing label is derived from the score."""
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({"score": 1.7, "feedback": "ok"})
        r = client.post("/api/v1/grade", json=GRADE_PAYLOAD)
    data = r.json()
    assert data["score"] == 1.0
    assert data["grade_label"] == "Отлично"


def test_grade_plain_text_fallback():
    with patch("app.services.llm_router.generate", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Code looks fine."
        r = client.post("/api/v1/grade", json=GRADE_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["feedback"] == "Code looks fine."
    assert data["score"] == 0.5
