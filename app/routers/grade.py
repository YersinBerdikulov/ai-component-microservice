from fastapi import APIRouter

from app.models.schemas import GradeRequest, GradeResponse
from app.prompts import grade_prompts
from app.services import llm_router
from app.services.json_utils import extract_json
from app.services.pilot_logger import log_event

router = APIRouter()

_GRADE_LABELS = [
    (0.85, "Отлично"),
    (0.70, "Хорошо"),
    (0.50, "Удовлетворительно"),
    (0.00, "Неудовлетворительно"),
]


def _label(score: float) -> str:
    for threshold, label in _GRADE_LABELS:
        if score >= threshold:
            return label
    return "Неудовлетворительно"


@router.post("/grade", response_model=GradeResponse)
async def grade_submission(request: GradeRequest):
    user_message = grade_prompts.build_user_prompt(
        task_description=request.task_description,
        expected_approach=request.expected_approach,
        submitted_code=request.submitted_code,
        execution_output=request.execution_result.output,
        execution_error=request.execution_result.error,
        vl_level=request.vl_level,
    )

    raw = await llm_router.generate(
        grade_prompts.SYSTEM_PROMPT,
        user_message,
        temperature=0.3,   # low temp — grading should be consistent
        max_tokens=1000,
    )

    try:
        data = extract_json(raw)
        score = max(0.0, min(1.0, float(data.get("score", 0.5))))
        response = GradeResponse(
            score=round(score, 2),
            grade_label=data.get("grade_label") or _label(score),
            is_correct=bool(data.get("is_correct", False)),
            feedback=data.get("feedback", raw),
            code_issues=data.get("code_issues", []),
            recommendations=data.get("recommendations", []),
        )
    except Exception:
        response = GradeResponse(
            score=0.5,
            grade_label="Удовлетворительно",
            is_correct=False,
            feedback=raw,
            code_issues=[],
            recommendations=[],
        )

    log_event("grade", {
        "teacher_id": request.teacher_id,
        "task_id": request.task_id,
        "score": response.score,
        "is_correct": response.is_correct,
        "had_error": bool(request.execution_result.error),
        "vl_level": request.vl_level,
    })
    return response
