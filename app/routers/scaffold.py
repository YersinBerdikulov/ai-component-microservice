from fastapi import APIRouter
from app.models.schemas import ScaffoldRequest, ScaffoldResponse
from app.services import llm_router
from app.services.json_utils import extract_json
from app.services.pilot_logger import log_event
from app.prompts import scaffold_prompts

router = APIRouter()


@router.post("/scaffold", response_model=ScaffoldResponse)
async def get_scaffold_hint(request: ScaffoldRequest):
    system_prompt = scaffold_prompts.SYSTEM_PROMPT
    user_message = scaffold_prompts.build_user_prompt(
        scenario_name=request.context.scenario_name,
        current_step=request.current_step,
        teacher_action=request.teacher_action,
        vl_level=request.vl_level,
        available_data=request.context.available_data,
        objective=request.context.objective,
    )

    raw = await llm_router.generate(system_prompt, user_message, temperature=0.7, max_tokens=600)

    try:
        data = extract_json(raw)
        response = ScaffoldResponse(**data)
    except Exception:
        response = ScaffoldResponse(
            hint=raw,
            hint_type="guiding_question",
            difficulty_adjusted=True,
            next_suggested_action="Продолжите анализ данных",
        )

    log_event("scaffold", {
        "teacher_id": request.teacher_id,
        "scenario_id": request.scenario_id,
        "current_step": request.current_step,
        "vl_level": request.vl_level,
        "hint_type": response.hint_type,
    })
    return response
