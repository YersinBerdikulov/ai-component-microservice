from fastapi import APIRouter

from app.ml import predictor
from app.models.schemas import PredictRequest, PredictResponse, StudentPrediction

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict_risks(request: PredictRequest):
    student_list = [s.model_dump() for s in request.student_data]
    results = predictor.predict(student_list)
    predictions = [StudentPrediction(**r) for r in results]
    return PredictResponse(predictions=predictions)
