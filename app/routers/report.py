from fastapi import APIRouter
from app.models.schemas import ReportRequest, ReportResponse
from app.services import llm_router
from app.services.json_utils import extract_json
from app.prompts import report_prompts

router = APIRouter()


@router.post("/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    user_message = report_prompts.build_user_prompt(
        scenario_id=request.scenario_id,
        decisions_log=[d.model_dump() for d in request.decisions_log],
        student_outcomes=[o.model_dump() for o in request.student_outcomes],
    )

    raw = await llm_router.generate(
        report_prompts.SYSTEM_PROMPT, user_message, temperature=0.5, max_tokens=1500
    )

    try:
        data = extract_json(raw)
        return ReportResponse(**data)
    except Exception:
        return ReportResponse(
            report_text=raw,
            strengths=[],
            areas_for_improvement=[],
            score=0.5,
        )
