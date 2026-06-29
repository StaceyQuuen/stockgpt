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