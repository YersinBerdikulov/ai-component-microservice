
from pydantic import BaseModel


class ScaffoldContext(BaseModel):
    scenario_name: str
    available_data: list[str]
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
    student_data: list[StudentData]


class StudentPrediction(BaseModel):
    student_id: str
    risk_score: float
    risk_level: str
    top_risk_factors: list[str]


class PredictResponse(BaseModel):
    predictions: list[StudentPrediction]


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
    decisions_log: list[DecisionLog]
    student_outcomes: list[StudentOutcome]


class ReportResponse(BaseModel):
    report_text: str
    strengths: list[str]
    areas_for_improvement: list[str]
    score: float


class VLResponse(BaseModel):
    question_id: str
    answer: str


class AssessVLRequest(BaseModel):
    teacher_id: str
    responses: list[VLResponse]


class AssessVLResponse(BaseModel):
    vl_level: str
    score: float
    recommended_dashboard_complexity: str
    weak_areas: list[str]


class TaskContext(BaseModel):
    current_step: str
    available_data: list[str]
    visible_dashboard: str | None = None
    scenario_objective: str


class ChatRequest(BaseModel):
    teacher_id: str
    scenario_id: str
    message: str
    task_context: TaskContext
    vl_level: str


class ChatResponse(BaseModel):
    reply: str
    suggested_actions: list[str]
    references: list[str]


class ExecutionResult(BaseModel):
    output: str | None = None   # stdout / query result as string
    error: str | None = None    # error message if code failed


class GradeRequest(BaseModel):
    teacher_id: str
    task_id: str
    task_description: str          # what the task asked the teacher to do
    expected_approach: str         # rubric / correct method description
    submitted_code: str            # the code the teacher wrote
    execution_result: ExecutionResult
    vl_level: str


class GradeResponse(BaseModel):
    score: float                   # 0.0 – 1.0
    grade_label: str               # "Отлично" | "Хорошо" | "Удовлетворительно" | "Неудовлетворительно"
    is_correct: bool
    feedback: str                  # main narrative feedback
    code_issues: list[str]         # specific code problems found
    recommendations: list[str]     # concrete next steps
