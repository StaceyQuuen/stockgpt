from app.services.stock_service import StockDataService
from app.core.logger import log


class FinancialAgent:

    def run(self, state):

        if state.get("financial_analysis"):

            return {}

        data = StockDataService().get_stock_info(state["stock_code"])

        analysis = f"""
财务分析：

PE: {data.financial.pe}
ROE: {data.financial.roe}
收盘价: {data.price.close}

结论：财务结构正常
"""

        return {

            "stock_data": data.dict(),

            "financial_analysis": analysis
        }