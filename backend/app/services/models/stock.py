from pydantic import BaseModel
from typing import List, Optional


class StockPrice(BaseModel):

    symbol: str

    close: float

    open: float

    high: float

    low: float

    volume: float


class FinancialData(BaseModel):

    roe: float | None = None

    pe: float | None = None

    revenue: float | None = None


class StockInfo(BaseModel):

    stock_code: str

    price: StockPrice

    financial: FinancialData


# ========== 短线分析新增模型 ==========

class KLineBar(BaseModel):
    """单根 K 线数据"""
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    turnover: float | None = None  # 换手率
    amount: float | None = None    # 成交额


class TechnicalIndicators(BaseModel):
    """技术指标汇总"""
    ma5: float | None = None
    ma10: float | None = None
    ma20: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    rsi: float | None = None
    boll_upper: float | None = None
    boll_mid: float | None = None
    boll_lower: float | None = None
    volume_ratio: float | None = None  # 量比
    trend: str | None = None           # 趋势判断


class MoneyFlow(BaseModel):
    """个股资金流向"""
    main_net_inflow: float | None = None
    retail_net_inflow: float | None = None
    super_large_net: float | None = None
    large_net: float | None = None


class ShortTermStrategy(BaseModel):
    """短线持仓策略"""
    entry_range: str
    stop_profit: str
    stop_loss: str
    position_ratio: str
    hold_days: str


class ShortTermAssessment(BaseModel):
    """短线适配性评估结果"""
    suitable: bool
    score: float
    reasons: List[str]
    strategy: ShortTermStrategy | None = None


class StockSearchResult(BaseModel):
    """股票搜索结果"""
    code: str
    name: str
