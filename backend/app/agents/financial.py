from app.services.stock_service import StockDataService
from app.core.logger import log


class FinancialAgent:

    def run(self, state):

        log.info("Financial Agent running")

        service = StockDataService()

        data = service.get_stock_info(state["stock_code"])

        analysis = f"""
财务分析：

PE: {data.financial.pe}
ROE: {data.financial.roe}
收盘价: {data.price.close}

结论：财务数据处于分析阶段（后续接LLM优化）
"""

        return {
            **state,
            "stock_data": data.dict(),
            "financial_analysis": analysis
        }