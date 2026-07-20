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

        # ========== 个股趋势结论 ==========
        trend_conclusion = "震荡"
        if trend == "多头排列":
            trend_conclusion = "上升趋势"
        elif trend == "空头排列":
            trend_conclusion = "下降趋势"
        # MACD 辅助
        if indicators.macd is not None and indicators.macd_signal is not None:
            if indicators.macd > indicators.macd_signal and trend != "空头排列":
                trend_conclusion += "（MACD 金叉确认）"
            elif indicators.macd < indicators.macd_signal and trend != "多头排列":
                trend_conclusion += "（MACD 死叉走弱）"
        # ========== 位置判断（低位/突破/回踩/高位）==========
        position_label = "数据不足"
        position_pct = None
        if len(kline_bars) >= 10:
            highs = [b.high for b in kline_bars]
            lows = [b.low for b in kline_bars]
            max_high = max(highs)
            min_low = min(lows)
            if max_high > min_low:
                position_pct = (current_price - min_low) / (max_high - min_low) * 100
                position_pct = round(position_pct, 1)

                if position_pct < 25:
                    position_label = "低位"
                elif position_pct >= 80:
                    position_label = "高位"
                else:
                    position_label = "中位"

                # 突破判断：价格突破近 20 日最高价
                if len(kline_bars) >= 20:
                    high_20 = max(b.high for b in kline_bars[-20:])
                    if current_price >= high_20 * 0.995:
                        position_label = "突破"

                # 回踩判断：价格在均线附近
                if indicators.ma5 and indicators.ma10:
                    near_ma5 = abs(current_price - indicators.ma5) / current_price < 0.01
                    near_ma10 = abs(current_price - indicators.ma10) / current_price < 0.015
                    if (near_ma5 or near_ma10) and position_label not in ("低位", "突破"):
                        position_label = "回踩"

        # ========== 量价关系结论（简短）==========
        vp_label = "数据不足"
        if len(kline_bars) >= 6:
            recent = kline_bars[-5:]
            prev = kline_bars[-10:-5] if len(kline_bars) >= 10 else kline_bars[:5]

            recent_avg_vol = sum(b.volume for b in recent) / len(recent)
            prev_avg_vol = sum(b.volume for b in prev) / len(prev) if prev else recent_avg_vol
            vol_change = (recent_avg_vol / prev_avg_vol - 1) * 100 if prev_avg_vol > 0 else 0

            recent_price_change = (recent[-1].close / recent[0].close - 1) * 100 if recent[0].close > 0 else 0

            if vol_change > 20 and recent_price_change > 1:
                vp_label = "放量上涨"
            elif vol_change > 20 and recent_price_change < -1:
                vp_label = "放量下跌"
            elif vol_change < -20 and recent_price_change > 0:
                vp_label = "缩量上涨"
            elif vol_change < -20 and recent_price_change < -1:
                vp_label = "缩量回调"
            elif vol_change < -20 and abs(recent_price_change) < 1:
                vp_label = "缩量横盘"
            else:
                vp_label = "量价平稳"

        # ========== 主力行为推断 ==========
        mp_text = "无法判断"
        if len(kline_bars) >= 10 and position_pct is not None:
            recent_5 = kline_bars[-5:]
            recent_vol = sum(b.volume for b in recent_5) / len(recent_5)
            prev_vol = sum(b.volume for b in kline_bars[-10:-5]) / 5

            vol_ratio_5 = recent_vol / prev_vol if prev_vol > 0 else 1
            price_chg_5 = (recent_5[-1].close / recent_5[0].close - 1) * 100

            if position_pct < 30 and vol_ratio_5 > 1.3 and abs(price_chg_5) < 3:
                mp_text = "疑似吸筹阶段：低位温和放量，价格小幅波动，可能有资金介入"
            elif position_pct < 50 and vol_ratio_5 < 0.7 and abs(price_chg_5) < 3:
                mp_text = "疑似洗盘阶段：缩量横盘，浮筹清洗，等待拉升信号"
            elif position_pct > 50 and vol_ratio_5 > 1.5 and price_chg_5 > 3:
                mp_text = "疑似拉升阶段：高位放量上涨，短期动能强劲"
            elif position_pct > 70 and vol_ratio_5 > 1.5 and price_chg_5 < -2:
                mp_text = "疑似派发阶段：高位放量下跌，主力可能出货"
            elif position_pct > 70 and vol_ratio_5 < 0.8 and price_chg_5 > 0:
                mp_text = "高位缩量上涨：上攻乏力，注意追高风险"
            else:
                mp_text = "暂无明显主力行为特征，处于震荡整理阶段"

        # ========== 构建分析文本（精简输出）==========
        signals_text = "\n".join(signals)

        analysis = f"""
技术分析（基于近 30 日 K 线）：

【个股趋势】{trend_conclusion}
【位置】{position_label}
【量价关系】{vp_label}
【主力行为】{mp_text}

详细指标：RSI={indicators.rsi}，量比={indicators.volume_ratio}，MACD DIF={indicators.macd}/DEA={indicators.macd_signal}

【综合信号】
{signals_text}
"""

        return {
            "indicators": indicators.model_dump(),
            "technical_analysis": analysis,
        }
