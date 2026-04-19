#!/bin/bash
BASE="http://localhost:8100/api/v1"

echo "=== Health ==="
curl -s http://localhost:8100/health | python -m json.tool

echo ""
echo "=== POST /assess-vl ==="
curl -s -X POST "$BASE/assess-vl" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": "t001",
    "responses": [
      {"question_id": "q1", "answer": "b"},
      {"question_id": "q2", "answer": "c"},
      {"question_id": "q3", "answer": "a"},
      {"question_id": "q4", "answer": "b"},
      {"question_id": "q5", "answer": "d"},
      {"question_id": "q6", "answer": "a"},
      {"question_id": "q7", "answer": "c"},
      {"question_id": "q8", "answer": "b"}
    ]
  }' | python -m json.tool

echo ""
echo "=== POST /predict ==="
curl -s -X POST "$BASE/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": [
      {"student_id": "s001", "attendance_rate": 0.95, "assignment_completion": 0.9, "avg_grade": 82, "forum_posts": 12, "time_on_platform": 15, "late_submissions": 1},
      {"student_id": "s002", "attendance_rate": 0.45, "assignment_completion": 0.3, "avg_grade": 38, "forum_posts": 0, "time_on_platform": 2, "late_submissions": 8}
    ]
  }' | python -m json.tool

echo ""
echo "=== POST /scaffold (requires LLM key) ==="
curl -s -X POST "$BASE/scaffold" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": "t001",
    "scenario_id": "case_attendance",
    "current_step": "data_exploration",
    "teacher_action": "Педагог открыл дашборд посещаемости",
    "vl_level": "beginner",
    "context": {
      "scenario_name": "Анализ посещаемости класса 9Б",
      "available_data": ["attendance_log", "grade_book", "demographic_info"],
      "objective": "Выявить студентов с риском отсева"
    }
  }' | python -m json.tool

echo ""
echo "=== POST /report (requires LLM key) ==="
curl -s -X POST "$BASE/report" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": "t001",
    "scenario_id": "case_attendance",
    "decisions_log": [
      {"step": 1, "action": "Посмотрел общую таблицу", "timestamp": "2025-04-01T10:00:00"},
      {"step": 2, "action": "Отфильтровал по посещаемости < 60%", "timestamp": "2025-04-01T10:05:00"},
      {"step": 3, "action": "Решил провести беседу со студентом s002", "timestamp": "2025-04-01T10:10:00"}
    ],
    "student_outcomes": [
      {"student_id": "s001", "final_grade": 85, "risk_level": "low"},
      {"student_id": "s002", "final_grade": 42, "risk_level": "high"}
    ]
  }' | python -m json.tool

echo ""
echo "=== POST /chat (requires LLM key + Redis) ==="
curl -s -X POST "$BASE/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": "t001",
    "scenario_id": "case_attendance",
    "message": "Как мне лучше проанализировать причины падения посещаемости?",
    "task_context": {
      "current_step": "data_exploration",
      "available_data": ["attendance_log", "grade_book", "demographic_info"],
      "visible_dashboard": "attendance_trend_chart",
      "scenario_objective": "Выявить студентов с риском отсева"
    },
    "vl_level": "intermediate"
  }' | python -m json.tool
