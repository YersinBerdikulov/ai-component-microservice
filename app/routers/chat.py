from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.prompts import chat_prompts
from app.services import chat_history, llm_router
from app.services.json_utils import extract_json
from app.services.pilot_logger import log_event

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    system_prompt = chat_prompts.build_system_prompt(
        vl_level=request.vl_level,
        scenario_objective=request.task_context.scenario_objective,
        current_step=request.task_context.current_step,
        available_data=request.task_context.available_data,
        visible_dashboard=request.task_context.visible_dashboard,
    )

    history = await chat_history.get_history(request.teacher_id, request.scenario_id)

    history_text = ""
    if history:
        lines = [
            f"{'Педагог' if m['role'] == 'user' else 'Ассистент'}: {m['content']}"
            for m in history[-10:]
        ]
        history_text = "История диалога:\n" + "\n".join(lines) + "\n\n"

    user_message = f"{history_text}Педагог: {request.message}"

    raw = await llm_router.generate(system_prompt, user_message, temperature=0.7, max_tokens=800, use_cache=False)

    try:
        data = extract_json(raw)
        reply = data.get("reply", raw)
        suggested_actions = data.get("suggested_actions", [])
        references = data.get("references", [])
    except Exception:
        reply = raw
        suggested_actions = []
        references = []

    await chat_history.save_message(request.teacher_id, request.scenario_id, request.message, reply)

    log_event("chat", {
        "teacher_id": request.teacher_id,
        "scenario_id": request.scenario_id,
        "vl_level": request.vl_level,
        "current_step": request.task_context.current_step,
        "n_suggested_actions": len(suggested_actions),
    })
    return ChatResponse(reply=reply, suggested_actions=suggested_actions, references=references)
