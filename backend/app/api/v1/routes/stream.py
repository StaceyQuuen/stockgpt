from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.stream_service import StreamAnalyzeService

router = APIRouter()

service = StreamAnalyzeService()


@router.post("/stream-analyze")
async def stream_analyze(req: dict):

    stock_code = req.get("stock_code")

    question = req.get("question")

    return StreamingResponse(

        service.stream(stock_code, question),

        media_type="text/plain"
    )