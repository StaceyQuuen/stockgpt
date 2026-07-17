from typing import TypedDict, Dict, Any, List


class GraphState(TypedDict):

    question: str

    stock_code: str

    stock_data: Dict[str, Any] | None

    news: List[str] | None

    technical: Dict[str, Any] | None

    risk: Dict[str, Any] | None

    financial_analysis: str | None

    news_analysis: str | None

    technical_analysis: str | None

    risk_analysis: str | None

    final_report: str | None

    # ⭐ 新增：并行控制字段
    analysis_ready: bool

    # ========== 短线分析新增字段 ==========
    kline_data: List[Dict[str, Any]] | None       # K线历史
    indicators: Dict[str, Any] | None             # 技术指标
    money_flow: Dict[str, Any] | None             # 资金流向
    short_term_assessment: Dict[str, Any] | None  # 短线评估结果
    short_term_analysis: str | None               # 短线分析文本
    stock_name: str | None                        # 股票名称
