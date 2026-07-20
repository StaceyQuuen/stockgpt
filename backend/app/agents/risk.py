from app.core.logger import log
from app.services.stock_service import StockDataService
from app.services.models.stock import KLineBar
import math


class RiskAgent:

    def run(self, state):
        log.info("Risk Agent running")

        stock_code = state.get("stock_code", "")
        service = StockDataService()

        # 优先从 state 读取 K 线（FinancialAgent 已预取）
        state_kline = state.get("kline_data")
        if state_kline:
            kline_bars = [KLineBar(**item) for item in state_kline]
        else:
            kline_bars = service.get_kline_data(stock_code, days=30)

        if len(kline_bars) < 5:
            analysis = """
风险分析：

K 线数据不足，无法进行有效风险评估。
该股票可能为新上市或停牌中。

结论：风险较高，建议谨慎
"""
            return {
                "risk": {
                    "volatility": "unknown",
                    "turnover_risk": "unknown",
                    "liquidity_risk": "unknown",
                },
                "risk_analysis": analysis,
            }

        # ========== 波动率计算 ==========
        closes = [b.close for b in kline_bars]
        returns = []
        for i in range(1, len(closes)):
            if closes[i - 1] > 0:
                r = (closes[i] - closes[i - 1]) / closes[i - 1]
                returns.append(r)

        if len(returns) >= 5:
            mean_r = sum(returns) / len(returns)
            variance = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
            daily_vol = math.sqrt(variance)
            annual_vol = daily_vol * math.sqrt(252)
        else:
            daily_vol = 0.0
            annual_vol = 0.0

        if annual_vol > 0.6:
            vol_level = "极高"
            vol_score = "高风险"
        elif annual_vol > 0.4:
            vol_level = "较高"
            vol_score = "中高风险"
        elif annual_vol > 0.25:
            vol_level = "中等"
            vol_score = "适中（适合短线）"
        else:
            vol_level = "较低"
            vol_score = "波动不足（不适合短线）"

        # ========== 换手率分析 ==========
        turnovers = [b.turnover for b in kline_bars if b.turnover is not None]
        avg_turnover = sum(turnovers) / len(turnovers) if turnovers else 0

        if avg_turnover < 1.0:
            turnover_risk = "换手率过低（<1%），流动性差，不适合短线"
            turnover_ok = False
        elif avg_turnover > 10.0:
            turnover_risk = "换手率过高（>10%），可能存在游资炒作，风险较大"
            turnover_ok = False
        else:
            turnover_risk = f"换手率正常（{avg_turnover:.1f}%），流动性良好"
            turnover_ok = True

        # ========== 流动性分析 ==========
        amounts = [b.amount for b in kline_bars if b.amount is not None]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        avg_amount_wan = avg_amount / 10000

        if avg_amount_wan < 5000:
            liquidity_risk = f"日均成交额 {avg_amount_wan:.0f} 万元，流动性不足"
            liquidity_ok = False
        else:
            liquidity_risk = f"日均成交额 {avg_amount_wan:.0f} 万元，流动性良好"
            liquidity_ok = True

        # ========== 近期涨跌幅 ==========
        if len(closes) >= 6:
            recent_return = (closes[-1] - closes[-6]) / closes[-6] * 100
        else:
            recent_return = 0

        if recent_return > 20:
            momentum_risk = f"近 5 日涨幅 {recent_return:.1f}%，短期涨幅过大，追高风险较高"
        elif recent_return < -15:
            momentum_risk = f"近 5 日跌幅 {recent_return:.1f}%，趋势向下，不宜接多"
        else:
            momentum_risk = f"近 5 日涨跌幅 {recent_return:.1f}%，动量正常"

        # ========== 最大回撤 ==========
        peak = closes[0]
        max_drawdown = 0
        for price in closes:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak * 100 if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # ========== 买点分析 ==========
        current_price = closes[-1]
        buy_signals = []
        buy_score = 0  # 0-5 满足条件数

        # 均线支撑
        if len(closes) >= 20:
            ma5 = sum(closes[-5:]) / 5
            ma10 = sum(closes[-10:]) / 10
            ma20 = sum(closes[-20:]) / 20
            if current_price <= ma5 * 1.01 and current_price >= ma5 * 0.99:
                buy_signals.append("✅ 价格回踩 MA5 支撑")
                buy_score += 1
            elif current_price <= ma10 * 1.01 and current_price >= ma10 * 0.99:
                buy_signals.append("✅ 价格回踩 MA10 支撑")
                buy_score += 1
            elif ma5 > ma10 > ma20:
                buy_signals.append("✅ 均线多头排列，趋势向上")
                buy_score += 1

        # 缩量企稳
        if len(kline_bars) >= 6:
            recent_vol = sum(b.volume for b in kline_bars[-3:]) / 3
            prev_vol = sum(b.volume for b in kline_bars[-6:-3]) / 3
            recent_chg = (closes[-1] / closes[-4] - 1) * 100 if closes[-4] > 0 else 0
            if recent_vol < prev_vol * 0.8 and abs(recent_chg) < 1.5:
                buy_signals.append("✅ 近 3 日缩量企稳，抛压减轻")
                buy_score += 1

        # RSI 超卖
        indicators = state.get("indicators", {})
        rsi = indicators.get("rsi") if indicators else None
        if rsi is not None:
            if rsi < 35:
                buy_signals.append(f"✅ RSI={rsi} 进入超卖区间，存在反弹机会")
                buy_score += 1
            elif rsi < 50:
                buy_signals.append(f"⚪ RSI={rsi} 中性偏低")
            elif rsi > 70:
                buy_signals.append(f"❌ RSI={rsi} 超买区间，追高风险大")

        if not buy_signals:
            buy_signals.append("⚪ 暂无明确买点信号")

        buy_point_text = "\n".join(buy_signals)
        buy_quality = "强" if buy_score >= 3 else "中" if buy_score >= 2 else "弱"

        # ========== 卖点/止盈止损分析 ==========
        sell_signals = []

        # 压力位（近 30 日最高点）
        highs = [b.high for b in kline_bars]
        max_high = max(highs)
        resistance = max_high
        resistance_pct = (resistance / current_price - 1) * 100 if current_price > 0 else 0

        # 支撑位（近 10 日最低点）
        lows_recent = [b.low for b in kline_bars[-10:]]
        min_low = min(lows_recent)
        support = min_low
        support_pct = (support / current_price - 1) * 100 if current_price > 0 else 0

        # 基于波动的止盈止损
        daily_vol_pct = daily_vol * 100
        tp_pct = max(daily_vol_pct * 3, 3.0)  # 至少 3%
        sl_pct = max(daily_vol_pct * 2, 2.0)  # 至少 2%

        take_profit = round(current_price * (1 + tp_pct / 100), 2)
        stop_loss = round(current_price * (1 - sl_pct / 100), 2)

        sell_signals.append(f"止盈目标: {take_profit}（+{tp_pct:.1f}%）")
        if resistance > current_price * 1.01:
            sell_signals.append(f"压力位: {resistance:.2f}（+{resistance_pct:.1f}%）")
        sell_signals.append(f"止损位: {stop_loss}（-{sl_pct:.1f}%）")
        if support < current_price * 0.99:
            sell_signals.append(f"支撑位: {support:.2f}（{support_pct:.1f}%）")
        if rsi is not None and rsi > 65:
            sell_signals.append(f"⚠️ RSI={rsi} 偏高，注意止盈")

        sell_point_text = "\n".join(sell_signals)

        # ========== 仓位管理建议 ==========
        if annual_vol < 0.2 or avg_turnover < 1.0:
            position_advice = "不建议短线：波动率过低或流动性不足，建议空仓观望"
        elif buy_score >= 3 and annual_vol > 0.25:
            position_advice = f"可建仓 30%-50%：买点信号较强（{buy_score}/5），可试探性建仓，确认走势后加仓"
        elif buy_score >= 2:
            position_advice = f"可建仓 20%-30%：买点信号一般（{buy_score}/5），轻仓试探，严格止损"
        elif recent_return > 15:
            position_advice = "建议空仓：短期涨幅过大，追高风险高，等待回调后再考虑"
        else:
            position_advice = f"建议观望或轻仓 10%-20%：买点信号弱（{buy_score}/5），等待更好的入场机会"

        analysis = f"""
风险评估（基于近 30 日数据）：

【波动率】
- 日波动率: {daily_vol * 100:.2f}%
- 年化波动率: {annual_vol * 100:.1f}%
- 波动等级: {vol_level}
- 短线评价: {vol_score}

【换手率】
- 平均换手率: {avg_turnover:.2f}%
- 评价: {turnover_risk}

【流动性】
- {liquidity_risk}

【近期动量】
- {momentum_risk}

【最大回撤】
- 近 30 日最大回撤: {max_drawdown:.1f}%

【买点分析】
{buy_point_text}
- 买点质量: {buy_quality}（满足 {buy_score}/5 条件）

【卖点规划】
{sell_point_text}

【仓位管理】
- {position_advice}

【综合风险等级】
- 波动: {vol_level}
- 换手: {"正常" if turnover_ok else "异常"}
- 流动性: {"正常" if liquidity_ok else "不足"}
"""

        return {
            "risk": {
                "annual_volatility": round(annual_vol * 100, 1),
                "daily_volatility": round(daily_vol * 100, 2),
                "volatility_level": vol_level,
                "avg_turnover": round(avg_turnover, 2),
                "turnover_ok": turnover_ok,
                "avg_amount_wan": round(avg_amount_wan, 0),
                "liquidity_ok": liquidity_ok,
                "recent_return": round(recent_return, 1),
                "max_drawdown": round(max_drawdown, 1),
                "buy_score": buy_score,
                "buy_quality": buy_quality,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "resistance": round(resistance, 2),
                "support": round(support, 2),
                "position_advice": position_advice,
            },
            "risk_analysis": analysis,
        }
