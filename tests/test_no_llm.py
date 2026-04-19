"""Tests for endpoints that do not require LLM or Redis."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_assess_vl_advanced():
    r = client.post("/api/v1/assess-vl", json={
        "teacher_id": "t001",
        "responses": [
            {"question_id": "q1", "answer": "b"},
            {"question_id": "q2", "answer": "c"},
            {"question_id": "q3", "answer": "a"},
            {"question_id": "q4", "answer": "b"},
            {"question_id": "q5", "answer": "d"},
            {"question_id": "q6", "answer": "a"},
            {"question_id": "q7", "answer": "c"},
            {"question_id": "q8", "answer": "b"},
        ],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["vl_level"] == "advanced"
    assert data["score"] == 1.0
    assert data["recommended_dashboard_complexity"] == "advanced"
    assert data["weak_areas"] == []


def test_assess_vl_beginner():
    r = client.post("/api/v1/assess-vl", json={
        "teacher_id": "t002",
        "responses": [
            {"question_id": "q1", "answer": "a"},
            {"question_id": "q2", "answer": "a"},
            {"question_id": "q3", "answer": "b"},
        ],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["vl_level"] == "beginner"


def test_predict():
    r = client.post("/api/v1/predict", json={
        "student_data": [
            {
                "student_id": "s001",
                "attendance_rate": 0.95,
                "assignment_completion": 0.9,
                "avg_grade": 82,
                "forum_posts": 12,
                "time_on_platform": 15,
                "late_submissions": 1,
            },
            {
                "student_id": "s002",
                "attendance_rate": 0.2,
                "assignment_completion": 0.1,
                "avg_grade": 20,
                "forum_posts": 0,
                "time_on_platform": 1,
                "late_submissions": 15,
            },
        ],
    })
    assert r.status_code == 200
    preds = r.json()["predictions"]
    assert len(preds) == 2
    ids = {p["student_id"] for p in preds}
    assert ids == {"s001", "s002"}
    levels = {p["student_id"]: p["risk_level"] for p in preds}
    assert levels["s001"] == "low"
    assert levels["s002"] == "high"
