from app.core.logger import log
from app.services.stock_service import StockDataService
from app.services.models.stock import KLineBar


class TechnicalAgent:

    def run(self, state):
        log.info("Technical Agent running")

        stock_code = state.get("stock_code", "")
        service = StockDataService()

        # 优先从 state 读取 K 线（FinancialAgent 已预取）
        state_kline = state.get("kline_data")
        if state_kline:
            kline_bars = [KLineBar(**item) for item in state_kline]
        else:
            kline_bars = service.get_kline_data(stock_code, days=30)

        indicators = service.get_technical_indicators(stock_code)
        current_price = kline_bars[-1].close if kline_bars else 0

        # ========== 信号分析 ==========
        signals = []

        # 趋势信号
        trend = indicators.trend or "未知"
        if trend == "多头排列":
            signals.append("✅ 均线多头排列，上升趋势明确")
        elif trend == "空头排列":
            signals.append("❌ 均线空头排列，下降趋势中")
        else:
            signals.append("⚪ 均线震荡排列，方向不明")

        # MACD 信号
        if indicators.macd is not None and indicators.macd_signal is not None:
            if indicators.macd > indicators.macd_signal:
                signals.append("✅ MACD 金叉状态，短期动能向上")
            else:
                signals.append("❌ MACD 死叉状态，短期动能减弱")
            if indicators.macd_hist is not None and indicators.macd_hist > 0:
                signals.append("📈 MACD 柱状图为正，买盘力量较强")

        # RSI 信号
        if indicators.rsi is not None:
            if indicators.rsi > 70:
                signals.append(f"⚠️ RSI={indicators.rsi}，进入超买区间，注意回调风险")
            elif indicators.rsi < 30:
                signals.append(f"💡 RSI={indicators.rsi}，进入超卖区间，可能存在反弹机会")
            else:
                signals.append(f"⚪ RSI={indicators.rsi}，处于中性区间")

        # 布林带信号
        if indicators.boll_upper and indicators.boll_lower and current_price:
            if current_price >= indicators.boll_upper:
                signals.append("⚠️ 价格触及布林上轨，短期压力较大")
            elif current_price <= indicators.boll_lower:
                signals.append("💡 价格触及布林下轨，短期可能存在支撑")
            else:
                signals.append("⚪ 价格在布林带内运行")

        # 量比信号
        if indicators.volume_ratio is not None:
            if indicators.volume_ratio > 2.0:
                signals.append(f"📊 量比={indicators.volume_ratio}，显著放量，关注突破有效性")
            elif indicators.volume_ratio < 0.5:
                signals.append(f"📊 量比={indicators.volume_ratio}，明显缩量，市场观望情绪浓")
            else:
                signals.append(f"⚪ 量比={indicators.volume_ratio}，成交量正常")

        # ========== 构建分析文本 ==========
        signals_text = "\n".join(signals)

        analysis = f"""
技术分析（基于近 30 日 K 线）：

【均线系统】
- MA5: {indicators.ma5}
- MA10: {indicators.ma10}
- MA20: {indicators.ma20}
- 趋势判断: {trend}

【MACD】
- DIF: {indicators.macd}
- DEA: {indicators.macd_signal}
- 柱状图: {indicators.macd_hist}

【RSI(14)】
- 数值: {indicators.rsi}

【布林带】
- 上轨: {indicators.boll_upper}
- 中轨: {indicators.boll_mid}
- 下轨: {indicators.boll_lower}

【量比】
- 数值: {indicators.volume_ratio}

【综合信号】
{signals_text}
"""

        return {
            "indicators": indicators.model_dump(),
            "technical_analysis": analysis,
        }
