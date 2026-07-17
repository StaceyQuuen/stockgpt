from pydantic import BaseModel
from typing import List, Optional


class ShortTermRequest(BaseModel):
    stock_code: str
    question: str = "分析这只股票是否适合短线操作"


class ShortTermStrategyResponse(BaseModel):
    entry_range: str | None = None
    stop_profit: str | None = None
    stop_loss: str | None = None
    position_ratio: str | None = None
    hold_days: str | None = None


class ShortTermAssessmentResponse(BaseModel):
    suitable: bool
    score: float
    reasons: List[str]
    strategy: ShortTermStrategyResponse | None = None


class StockSearchResponse(BaseModel):
    code: str
    name: str
