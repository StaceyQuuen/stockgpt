from app.services.stock_service import StockDataService
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.core.logger import log


class AnalyzeService:

    def __init__(self):

        self.stock_service = StockDataService()


    def analyze(self, req: AnalyzeRequest) -> AnalyzeResponse:

        log.info(f"Fetching stock data: {req.stock_code}")

        stock_info = self.stock_service.get_stock_info(req.stock_code)

        log.info("Stock data fetched")

        report = f"""
股票代码: {stock_info.stock_code}

收盘价: {stock_info.price.close}

PE: {stock_info.financial.pe}

ROE: {stock_info.financial.roe}

（AI分析后续接入 LangGraph）
"""

        return AnalyzeResponse(
            stock_code=req.stock_code,
            report=report
        )