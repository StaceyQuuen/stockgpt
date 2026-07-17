from app.services.stock_service import StockDataService
from app.core.logger import log


class FinancialAgent:

    def run(self, state):

        if state.get("financial_analysis"):
            return {}

        svc = StockDataService()
        data = svc.get_stock_info(state["stock_code"])

        # 预取 K 线数据（存入 state，供后续 technical/risk 节点复用，避免重复请求）
        kline_bars = svc.get_kline_data(state["stock_code"], days=30)
        kline_data = [b.model_dump() for b in kline_bars]

        # 尝试获取股票名称（如果 state 中没有）
        stock_name = state.get("stock_name") or ""
        if not stock_name:
            try:
                stock_name = svc.get_stock_name(state["stock_code"]) or ""
            except Exception:
                pass

        analysis = f"""
财务分析：

PE: {data.financial.pe}
ROE: {data.financial.roe}
收盘价: {data.price.close}
市值: {data.financial.revenue}
K线数据: {len(kline_bars)} 条

结论：财务结构正常
"""

        return {
            "stock_data": data.model_dump(),
            "financial_analysis": analysis,
            "stock_name": stock_name,
            "kline_data": kline_data,
        }
