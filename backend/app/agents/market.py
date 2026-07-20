from app.core.logger import log
from app.services.stock_service import StockDataService


class MarketAgent:
    """大盘环境分析 Agent — 分析上证指数走势，判断市场强弱"""

    def run(self, state):
        log.info("Market Agent running - 分析大盘环境")

        service = StockDataService()
        market = service.get_market_data(days=20)

        if not market:
            analysis = """
大盘环境分析：

数据获取失败，无法评估大盘环境。
建议关注上证指数走势后再做决策。
"""
            return {"market_analysis": analysis}

        close = market.get("latest_close", 0)
        ma5 = market.get("ma5")
        ma10 = market.get("ma10")
        ma20 = market.get("ma20")
        ret_5d = market.get("return_5d", 0)
        ret_20d = market.get("return_20d", 0)
        vol_ratio = market.get("volume_ratio")

        # 判断市场强弱
        if ma5 and ma10 and ma20:
            if ma5 > ma10 > ma20:
                market_trend = "强势市场"
                trend_detail = "均线多头排列（MA5 > MA10 > MA20），大盘处于上升趋势"
            elif ma5 < ma10 < ma20:
                market_trend = "弱势市场"
                trend_detail = "均线空头排列（MA5 < MA10 < MA20），大盘处于下降趋势"
            else:
                market_trend = "震荡市场"
                trend_detail = "均线交织，大盘方向不明，处于震荡整理"
        else:
            market_trend = "数据不足"
            trend_detail = "均线数据不完整"

        # 量能分析
        if vol_ratio is not None:
            if vol_ratio > 1.3:
                vol_text = f"近期成交量放大（量比 {vol_ratio}），市场活跃度提升"
            elif vol_ratio < 0.7:
                vol_text = f"近期成交量萎缩（量比 {vol_ratio}），市场观望情绪浓厚"
            else:
                vol_text = f"成交量平稳（量比 {vol_ratio}），市场情绪中性"
        else:
            vol_text = "成交量数据缺失"

        # 短线操作建议
        if market_trend == "强势市场":
            op_advice = "大盘环境有利于短线操作，可适当参与"
        elif market_trend == "弱势市场":
            op_advice = "大盘环境不利，短线操作风险较高，建议降低仓位或空仓"
        else:
            op_advice = "大盘震荡，短线需精选个股，控制仓位"

        analysis = f"""
大盘环境分析（上证指数 {close:.2f}，{market.get('latest_date', '')}）：

【市场趋势】
- {market_trend}：{trend_detail}
- 近 5 日涨跌: {ret_5d:+.2f}%
- 近 20 日涨跌: {ret_20d:+.2f}%

【大盘均线】
- MA5: {ma5}
- MA10: {ma10}
- MA20: {ma20}

【市场量能】
- {vol_text}

【短线环境评估】
- {op_advice}
"""

        return {"market_analysis": analysis}
