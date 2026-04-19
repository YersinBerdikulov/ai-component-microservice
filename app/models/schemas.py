from pydantic import BaseModel
from typing import Optional, List


class ScaffoldContext(BaseModel):
    scenario_name: str
    available_data: List[str]
    objective: str


class ScaffoldRequest(BaseModel):
    teacher_id: str
    scenario_id: str
    current_step: str
    teacher_action: str
    vl_level: str
    context: ScaffoldContext


class ScaffoldResponse(BaseModel):
    hint: str
    hint_type: str
    difficulty_adjusted: bool
    next_suggested_action: str


class StudentData(BaseModel):
    student_id: str
    attendance_rate: float
    assignment_completion: float
    avg_grade: float
    forum_posts: int
    time_on_platform: float
    late_submissions: int


class PredictRequest(BaseModel):
    student_data: List[StudentData]


class StudentPrediction(BaseModel):
    student_id: str
    risk_score: float
    risk_level: str
    top_risk_factors: List[str]


class PredictResponse(BaseModel):
    predictions: List[StudentPrediction]


class DecisionLog(BaseModel):
    step: int
    action: str
    timestamp: str


class StudentOutcome(BaseModel):
    student_id: str
    final_grade: float
    risk_level: str


class ReportRequest(BaseModel):
    teacher_id: str
    scenario_id: str
    decisions_log: List[DecisionLog]
    student_outcomes: List[StudentOutcome]


class ReportResponse(BaseModel):
    report_text: str
    strengths: List[str]
    areas_for_improvement: List[str]
    score: float


class VLResponse(BaseModel):
    question_id: str
    answer: str


class AssessVLRequest(BaseModel):
    teacher_id: str
    responses: List[VLResponse]


class AssessVLResponse(BaseModel):
    vl_level: str
    score: float
    recommended_dashboard_complexity: str
    weak_areas: List[str]


class TaskContext(BaseModel):
    current_step: str
    available_data: List[str]
    visible_dashboard: Optional[str] = None
    scenario_objective: str


class ChatRequest(BaseModel):
    teacher_id: str
    scenario_id: str
    message: str
    task_context: TaskContext
    vl_level: str


class ChatResponse(BaseModel):
    reply: str
    suggested_actions: List[str]
    references: List[str]
