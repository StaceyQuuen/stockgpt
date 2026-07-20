from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.schemas.short_term import (
    ShortTermRequest,
    ShortTermAssessmentResponse,
    StockSearchResponse,
)
from app.services.short_term_service import ShortTermStreamService
from app.services.stock_service import StockDataService
from app.services.pool_service import PoolService

router = APIRouter()

stream_service = ShortTermStreamService()
stock_service = StockDataService()
pool_service = PoolService()


@router.post("/short-term-analyze")
async def short_term_analyze(req: ShortTermRequest):
    """流式返回短线分析结果"""
    return StreamingResponse(
        stream_service.stream(req.stock_code, req.question),
        media_type="text/plain",
    )


@router.get("/stock/search", response_model=list[StockSearchResponse])
async def search_stock(q: str = Query(..., min_length=1, description="股票代码或名称")):
    """股票模糊搜索"""
    results = stock_service.search_stock(q)
    return [StockSearchResponse(code=r.code, name=r.name) for r in results]


@router.get("/stock-pool")
async def get_stock_pool():
    """获取短线股票池（三种买入形态）"""
    return pool_service.scan()
