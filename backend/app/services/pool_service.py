"""
短线股票池扫描服务 — 8 维度综合打分制
市场环境(10) + 热点板块(15) + 趋势(20) + 成交量(15) + 突破形态(15) + 资金流(10) + 换手率(5) + 风险收益比(10) = 100
"""
import datetime
import math
import pandas as pd

from app.services.repositories.akshare_repo import AkShareRepository
from app.core.cache import Cache
from app.core.logger import log

cache = Cache()


class PoolService:

    def __init__(self):
        self.repo = AkShareRepository()
        self._market_score = 5  # default neutral
        self._market_detail = ""
        self._hot_sectors: set[str] = set()

    # ================================================================
    # 主入口
    # ================================================================

    def scan(self) -> dict:
        cache_key = "stock_pool:scan_v2"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. 全市场快照
        spot_df = self.repo.get_all_spot_data()
        if spot_df is None or spot_df.empty:
            return self._empty_result("无法获取全市场行情数据")

        # 2. 大盘环境评分
        self._score_market()

        # 3. 热点板块（可选）
        self._load_hot_sectors()

        # 4. 初筛
        candidates = self._pre_filter(spot_df)
        if not candidates:
            return self._empty_result("初筛后无候选股票")

        # 5. 并发获取 K 线
        symbols = [c["code"] for c in candidates[:60]]
        kline_map = self.repo.batch_get_kline_sina(symbols, days=30, max_workers=10)
        if not kline_map:
            return self._empty_result("无法获取候选股票 K 线数据")

        # 6. 逐只打分
        name_map = {c["code"]: c["name"] for c in candidates}
        info_map = {c["code"]: c for c in candidates}
        scored = []

        for sym, df in kline_map.items():
            if len(df) < 15:
                continue

            closes = df["收盘"].astype(float).tolist()
            highs = df["最高"].astype(float).tolist()
            lows = [float(x) for x in df["最低"].tolist()] if "最低" in df.columns else [c * 0.99 for c in closes]
            volumes = df["成交量"].astype(float).tolist()
            turnover_col = "换手率" if "换手率" in df.columns else None
            turnovers = [float(x) for x in df[turnover_col].tolist()] if turnover_col and df[turnover_col].sum() > 0 else []

            scores = self._score_stock(closes, highs, lows, volumes, turnovers, info_map.get(sym, {}))
            total = sum(scores.values())

            info = info_map.get(sym, {})
            scored.append({
                "code": sym,
                "name": name_map.get(sym, ""),
                "price": info.get("price", round(closes[-1], 2)),
                "change_pct": info.get("change_pct", 0),
                "total_score": round(total, 1),
                "scores": scores,
                "star": self._to_star(total),
            })

        # 按总分降序
        scored.sort(key=lambda x: x["total_score"], reverse=True)

        # 只保留 40 分以上的
        top = [s for s in scored if s["total_score"] >= 40][:20]

        result = {
            "stocks": top,
            "market_score": self._market_score,
            "market_detail": self._market_detail,
            "scan_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_scanned": len(kline_map),
            "error": None,
        }

        cache.set(cache_key, result, ttl=300)
        return result

    # ================================================================
    # 市场环境评分 (10 分)
    # ================================================================

    def _score_market(self):
        market = self.repo.get_market_index(days=20)
        if not market:
            self._market_score = 5
            self._market_detail = "大盘数据不可用"
            return

        close = market.get("latest_close", 0)
        ma20 = market.get("ma20")
        ma5 = market.get("ma5")
        ret5 = market.get("return_5d", 0) or 0

        score = 3  # base
        details = []

        if ma20 and close > ma20:
            score += 3
            details.append("指数在20日均线上方")
        else:
            details.append("指数在20日均线下方")

        if ma5 and ma20 and ma5 > ma20:
            score += 2
            details.append("5日均线向上")

        if ret5 > 0:
            score += 2
            details.append(f"5日涨{ret5:.1f}%")
        elif ret5 < -3:
            score -= 1
            details.append(f"5日跌{abs(ret5):.1f}%，弱势")

        self._market_score = min(10, max(0, score))
        self._market_detail = "，".join(details)

    # ================================================================
    # 热点板块加载 (可选)
    # ================================================================

    def _load_hot_sectors(self):
        try:
            import akshare as ak
            df = ak.stock_board_concept_name_em()
            if df is not None and not df.empty:
                # 按涨跌幅排序取前 10 个热门概念
                chg_col = "涨跌幅" if "涨跌幅" in df.columns else None
                if chg_col:
                    df[chg_col] = pd.to_numeric(df[chg_col], errors="coerce")
                    df = df.sort_values(chg_col, ascending=False)
                name_col = "板块名称" if "板块名称" in df.columns else df.columns[1]
                self._hot_sectors = set(df[name_col].head(10).tolist())
        except Exception:
            self._hot_sectors = set()

    # ================================================================
    # 初筛
    # ================================================================

    def _pre_filter(self, df: pd.DataFrame) -> list[dict]:
        try:
            name_col = "名称" if "名称" in df.columns else None
            if name_col:
                df = df[~df[name_col].str.contains("ST|退|N", na=False, regex=True)]

            price_col = "最新价" if "最新价" in df.columns else None
            if price_col:
                df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
                df = df[df[price_col] > 0]

            turnover_col = "换手率" if "换手率" in df.columns else None
            has_turnover = False
            if turnover_col:
                df[turnover_col] = pd.to_numeric(df[turnover_col], errors="coerce")
                if df[turnover_col].sum() > 0:
                    df = df[df[turnover_col] > 2]
                    has_turnover = True

            amount_col = "成交额" if "成交额" in df.columns else None
            if amount_col:
                df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
                threshold = 30_000_000 if has_turnover else 50_000_000
                df = df[df[amount_col] > threshold]

            chg_col = "涨跌幅" if "涨跌幅" in df.columns else None
            if chg_col:
                df[chg_col] = pd.to_numeric(df[chg_col], errors="coerce")
                df = df[(df[chg_col] > -8) & (df[chg_col] < 8)]

            code_col = "代码" if "代码" in df.columns else None
            if code_col:
                df = df[~df[code_col].str.startswith(("8", "4", "688"))]

            sort_col = turnover_col if has_turnover else amount_col
            if sort_col and sort_col in df.columns:
                df = df.sort_values(sort_col, ascending=False).head(60)

            results = []
            for _, row in df.iterrows():
                results.append({
                    "code": str(row.get("代码", "")),
                    "name": str(row.get("名称", "")),
                    "price": float(row.get("最新价", 0)),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "turnover": float(row.get("换手率", 0)),
                    "amount": float(row.get("成交额", 0)),
                })
            return results
        except Exception as e:
            log.warning(f"PoolService 初筛失败: {e}")
            return []

    # ================================================================
    # 个股 8 维度打分
    # ================================================================

    def _score_stock(self, closes, highs, lows, volumes, turnovers, info) -> dict:
        n = len(closes)
        current = closes[-1]

        # 均线
        ma5 = sum(closes[-5:]) / 5 if n >= 5 else current
        ma10 = sum(closes[-10:]) / 10 if n >= 10 else current
        ma20 = sum(closes[-20:]) / 20 if n >= 20 else current

        # --- 1. 市场环境 (10) ---
        s_market = self._market_score

        # --- 2. 热点板块 (15) ---
        s_sector = self._score_sector(info)

        # --- 3. 趋势 (20) ---
        s_trend = self._score_trend(closes, highs, lows, ma5, ma10, ma20, current)

        # --- 4. 成交量 (15) ---
        s_volume = self._score_volume(closes, volumes)

        # --- 5. 突破形态 (15) ---
        s_breakout = self._score_breakout(closes, highs, lows, current, n)

        # --- 6. 资金流 (10) ---
        s_capital = self._score_capital_flow(closes, volumes)

        # --- 7. 换手率 (5) ---
        s_turnover = self._score_turnover(turnovers)

        # --- 8. 风险收益比 (10) ---
        s_rr = self._score_risk_reward(closes, highs, lows, current)

        return {
            "market": s_market,
            "sector": s_sector,
            "trend": s_trend,
            "volume": s_volume,
            "breakout": s_breakout,
            "capital": s_capital,
            "turnover": s_turnover,
            "risk_reward": s_rr,
        }

    # --- 2. 热点板块 (15) ---
    def _score_sector(self, info: dict) -> int:
        """基于概念板块热度评分"""
        if not self._hot_sectors:
            return 8  # 无法获取板块数据时给中等分
        # 简化：暂时无法精确映射个股→板块，给中等分
        # 后续可接入板块成分股映射提升精度
        return 8

    # --- 3. 趋势 (20) ---
    @staticmethod
    def _score_trend(closes, highs, lows, ma5, ma10, ma20, current) -> int:
        score = 0

        # 均线多头排列 (0-8)
        if ma5 > ma10 > ma20:
            score += 8
        elif ma5 > ma10:
            score += 5
        elif ma5 < ma10 < ma20:
            score += 0
        else:
            score += 3

        # 价格在 20 日均线上方 (0-4)
        if current > ma20:
            score += 4
        elif current > ma20 * 0.98:
            score += 2

        # 高点不断抬高 (0-4)
        if len(highs) >= 20:
            recent_high = max(highs[-5:])
            prev_high = max(highs[-15:-5])
            if recent_high > prev_high:
                score += 4
            elif recent_high > prev_high * 0.98:
                score += 2

        # 低点不断抬高 (0-4)
        if len(lows) >= 20:
            recent_low = min(lows[-5:])
            prev_low = min(lows[-15:-5])
            if recent_low > prev_low:
                score += 4
            elif recent_low > prev_low * 0.98:
                score += 2

        return min(20, score)

    # --- 4. 成交量 (15) ---
    @staticmethod
    def _score_volume(closes, volumes) -> int:
        if len(volumes) < 10 or len(closes) < 10:
            return 5

        score = 0
        n = len(volumes)

        # 近 5 日 vs 前 5 日量比
        recent_vol = sum(volumes[-5:]) / 5
        prev_vol = sum(volumes[-10:-5]) / 5 if n >= 10 else recent_vol
        vol_ratio = recent_vol / prev_vol if prev_vol > 0 else 1

        recent_chg = (closes[-1] / closes[-5] - 1) * 100 if closes[-5] > 0 else 0

        # 放量上涨 (0-6)
        if vol_ratio > 1.5 and recent_chg > 1:
            score += 6
        elif vol_ratio > 1.2 and recent_chg > 0:
            score += 4
        elif vol_ratio > 1.0 and recent_chg > 0:
            score += 2

        # 上涨放量 + 回调缩量 (0-5)
        # 检查近 5 日中上涨日是否量大于下跌日
        up_vol, down_vol = [], []
        for i in range(-5, 0):
            if closes[i] > closes[i - 1]:
                up_vol.append(volumes[i])
            else:
                down_vol.append(volumes[i])

        if up_vol and down_vol:
            avg_up = sum(up_vol) / len(up_vol)
            avg_down = sum(down_vol) / len(down_vol)
            if avg_up > avg_down * 1.3:
                score += 5
            elif avg_up > avg_down:
                score += 3
        elif up_vol and not down_vol:
            score += 5  # 全涨

        # 缩量回调是好信号 (0-4)
        if n >= 6:
            last3_vol = sum(volumes[-3:]) / 3
            prev3_vol = sum(volumes[-6:-3]) / 3
            last3_chg = (closes[-1] / closes[-3] - 1) * 100 if closes[-3] > 0 else 0
            if last3_vol < prev3_vol * 0.7 and abs(last3_chg) < 2:
                score += 4  # 缩量企稳
            elif last3_vol < prev3_vol * 0.85 and last3_chg > -1:
                score += 2

        return min(15, score)

    # --- 5. 突破形态 (15) ---
    @staticmethod
    def _score_breakout(closes, highs, lows, current, n) -> int:
        if n < 15:
            return 5

        score = 0

        # 30 日位置百分比
        max_high = max(highs)
        min_low = min(lows) if lows else current
        range_val = max_high - min_low
        pos_pct = (current - min_low) / range_val * 100 if range_val > 0 else 50

        # 平台突破检测 (0-8)
        if n >= 15:
            # 近 10 日区间（不含今日）
            range_high_10 = max(highs[-11:-1])
            range_low_10 = min(closes[-11:-1])
            amplitude = (range_high_10 - range_low_10) / range_low_10 * 100 if range_low_10 > 0 else 99

            if amplitude < 8 and current > range_high_10:
                score += 8  # 窄幅横盘后突破
            elif amplitude < 12 and current > range_high_10:
                score += 6  # 较宽横盘后突破
            elif current >= range_high_10 * 0.995:
                score += 4  # 接近突破

        # 回踩支撑 (0-4)
        if n >= 20:
            ma5 = sum(closes[-5:]) / 5
            ma10 = sum(closes[-10:]) / 10
            dist_ma5 = abs(current - ma5) / current * 100
            dist_ma10 = abs(current - ma10) / current * 100

            if dist_ma5 < 1.0:
                score += 4  # 精确回踩 MA5
            elif dist_ma10 < 1.5:
                score += 3  # 回踩 MA10
            elif dist_ma5 < 2.0:
                score += 2

        # 位置适中 (0-3) — 不追高
        if 20 < pos_pct < 70:
            score += 3
        elif pos_pct <= 20:
            score += 2  # 低位也行
        elif pos_pct > 85:
            score += 0  # 太高，不追

        return min(15, score)

    # --- 6. 资金流 (10) ---
    @staticmethod
    def _score_capital_flow(closes, volumes) -> int:
        """基于量价模式推断资金行为"""
        if len(closes) < 10 or len(volumes) < 10:
            return 4

        score = 0
        n = len(closes)

        # 上涨日放量（资金流入信号）
        up_big_vol_days = 0
        down_big_vol_days = 0
        for i in range(-5, 0):
            avg_vol = sum(volumes[max(0, i - 5):i]) / min(5, abs(i))
            if avg_vol > 0:
                ratio = volumes[i] / avg_vol
                if closes[i] > closes[i - 1] and ratio > 1.3:
                    up_big_vol_days += 1
                elif closes[i] < closes[i - 1] and ratio > 1.3:
                    down_big_vol_days += 1

        # 上涨放量天数 (0-4)
        score += min(4, up_big_vol_days * 2)

        # 下跌不放量是好信号 (0-3)
        if down_big_vol_days == 0:
            score += 3
        elif down_big_vol_days <= 1:
            score += 1

        # 回调有承接：低点附近有放量 (0-3)
        if n >= 10:
            low_idx = closes.index(min(closes[-10:]))
            if low_idx >= n - 10:
                local_idx = low_idx - (n - 10)
                if local_idx < len(volumes):
                    avg_v = sum(volumes[-10:]) / 10
                    if volumes[low_idx] > avg_v * 1.2:
                        score += 3
                    elif volumes[low_idx] > avg_v:
                        score += 1

        return min(10, score)

    # --- 7. 换手率 (5) ---
    @staticmethod
    def _score_turnover(turnovers) -> int:
        if not turnovers or len(turnovers) < 5:
            return 2  # 无数据时给中等分

        avg_t = sum(turnovers[-5:]) / min(5, len(turnovers[-5:]))

        if 5 <= avg_t <= 15:
            return 5  # 趋势股理想区间
        elif 3 <= avg_t < 5 or 15 < avg_t <= 20:
            return 3
        elif avg_t < 3:
            return 1  # 不活跃
        else:
            return 2  # 太高，分歧大

    # --- 8. 风险收益比 (10) ---
    @staticmethod
    def _score_risk_reward(closes, highs, lows, current) -> int:
        if len(closes) < 10:
            return 4

        # 压力位：近 20 日最高
        resistance = max(highs[-20:]) if len(highs) >= 20 else max(highs)
        # 支撑位：近 10 日最低
        support = min(lows[-10:]) if len(lows) >= 10 else min(lows)

        upside = resistance - current
        downside = current - support

        if downside <= 0:
            return 3  # 价格在支撑位，风险低但空间也小

        ratio = upside / downside if downside > 0 else 0

        if ratio >= 2.5:
            return 10
        elif ratio >= 2.0:
            return 8
        elif ratio >= 1.5:
            return 6
        elif ratio >= 1.0:
            return 4
        else:
            return 2

    # ================================================================
    # 工具方法
    # ================================================================

    @staticmethod
    def _to_star(score: float) -> str:
        if score >= 80:
            return "★★★★★"
        elif score >= 60:
            return "★★★"
        elif score >= 40:
            return "★★"
        else:
            return "★"

    @staticmethod
    def _empty_result(error_msg: str) -> dict:
        return {
            "stocks": [],
            "market_score": 0,
            "market_detail": error_msg,
            "scan_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_scanned": 0,
            "error": error_msg,
        }
