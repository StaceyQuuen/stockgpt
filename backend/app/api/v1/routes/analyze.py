from fastapi import APIRouter

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.analyze_service import AnalyzeService


router = APIRouter()

service = AnalyzeService()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):

    return service.analyze(req)