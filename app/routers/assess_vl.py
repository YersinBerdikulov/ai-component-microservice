from fastapi import APIRouter
from app.models.schemas import AssessVLRequest, AssessVLResponse

router = APIRouter()

# Rule-based: correct answers and topic area per question
QUESTIONS = {
    "q1": {"correct": "b", "area": "Чтение базовых графиков"},
    "q2": {"correct": "c", "area": "Выявление трендов"},
    "q3": {"correct": "a", "area": "Интерпретация статистических визуализаций"},
    "q4": {"correct": "b", "area": "Понимание корреляции"},
    "q5": {"correct": "d", "area": "Чтение тепловых карт"},
    "q6": {"correct": "a", "area": "Анализ scatter plot"},
    "q7": {"correct": "c", "area": "Работа с многоуровневыми дашбордами"},
    "q8": {"correct": "b", "area": "Принятие решений на основе данных"},
}


@router.post("/assess-vl", response_model=AssessVLResponse)
async def assess_vl(request: AssessVLRequest):
    correct_count = 0
    weak_areas = []

    for response in request.responses:
        qid = response.question_id
        if qid not in QUESTIONS:
            continue
        q = QUESTIONS[qid]
        if response.answer == q["correct"]:
            correct_count += 1
        else:
            weak_areas.append(q["area"])

    score = correct_count / len(QUESTIONS)

    if score >= 0.75:
        vl_level = "advanced"
        complexity = "advanced"
    elif score >= 0.45:
        vl_level = "intermediate"
        complexity = "standard"
    else:
        vl_level = "beginner"
        complexity = "simple"

    return AssessVLResponse(
        vl_level=vl_level,
        score=round(score, 2),
        recommended_dashboard_complexity=complexity,
        weak_areas=weak_areas,
    )
