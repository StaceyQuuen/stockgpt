from app.services.repositories.akshare_repo import AkShareRepository
from app.services.models.stock import (
    StockInfo, StockPrice, FinancialData,
    KLineBar, TechnicalIndicators, MoneyFlow, StockSearchResult,
)
from app.core.cache import Cache
from app.core.logger import log

import pandas as pd

cache = Cache()


class StockDataService:

    def __init__(self):
        self.repo = AkShareRepository()

    def get_stock_info(self, stock_code: str) -> StockInfo:
        cache_key = f"stock_info:{stock_code}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return StockInfo(**cached_data) if isinstance(cached_data, dict) else cached_data

        price_dict = {}
        fin_dict = {}

        try:
            price_dict = self.repo.get_stock_price(stock_code) or {}
        except Exception as e:
            log.warning(f"akshare get_stock_price failed: {e}")

        try:
            fin_dict = self.repo.get_financial(stock_code) or {}
        except Exception as e:
            log.warning(f"akshare get_financial failed: {e}")

        price = StockPrice(
            symbol=price_dict.get("symbol", stock_code),
            open=price_dict.get("open", 0.0),
            close=price_dict.get("close", 0.0),
            high=price_dict.get("high", 0.0),
            low=price_dict.get("low", 0.0),
            volume=price_dict.get("volume", 0.0),
        )

        pe = self._extract_number(fin_dict, ["市盈率", "pe", "PE"])
        roe = self._extract_number(fin_dict, ["净资产收益率", "roe", "ROE"])
        revenue = self._extract_number(fin_dict, ["营业收入", "revenue"])

        financial = FinancialData(pe=pe, roe=roe, revenue=revenue)
        stock_info = StockInfo(stock_code=stock_code, price=price, financial=financial)

        cache.set(cache_key, stock_info.model_dump(), ttl=600)
        return stock_info

    # ========== 短线分析新增方法 ==========

    def get_kline_data(self, stock_code: str, days: int = 30) -> list[KLineBar]:
        """获取近 N 日 K 线数据"""
        cache_key = f"kline:{stock_code}:{days}"
        cached = cache.get(cache_key)
        if cached:
            return [KLineBar(**item) for item in cached]

        raw = self.repo.get_hist_kline(stock_code, days)
        if not raw:
            return []

        bars = [KLineBar(**item) for item in raw]
        cache.set(cache_key, [b.model_dump() for b in bars], ttl=300)
        return bars

    def get_technical_indicators(self, stock_code: str) -> TechnicalIndicators:
        """基于 30 日 K 线计算技术指标"""
        cache_key = f"tech_ind:{stock_code}"
        cached = cache.get(cache_key)
        if cached:
            return TechnicalIndicators(**cached)

        bars = self.get_kline_data(stock_code, days=30)
        if len(bars) < 5:
            log.warning(f"K 线数据不足，无法计算技术指标：{stock_code}")
            return TechnicalIndicators()

        df = pd.DataFrame([{
            "close": b.close, "high": b.high, "low": b.low, "volume": b.volume,
        } for b in bars])

        closes = df["close"]
        volumes = df["volume"]

        # 均线
        ma5 = closes.rolling(5).mean().iloc[-1] if len(closes) >= 5 else None
        ma10 = closes.rolling(10).mean().iloc[-1] if len(closes) >= 10 else None
        ma20 = closes.rolling(20).mean().iloc[-1] if len(closes) >= 20 else None

        # MACD
        ema12 = closes.ewm(span=12, adjust=False).mean()
        ema26 = closes.ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        macd_hist = 2 * (dif - dea)

        macd_val = float(dif.iloc[-1]) if not dif.empty else None
        macd_signal = float(dea.iloc[-1]) if not dea.empty else None
        macd_hist_val = float(macd_hist.iloc[-1]) if not macd_hist.empty else None

        # RSI（14 日）
        delta = closes.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss.replace(0, float("nan"))
        rsi_series = 100 - (100 / (1 + rs))
        rsi_val = float(rsi_series.iloc[-1]) if len(rsi_series) >= 14 else None

        # 布林带
        if len(closes) >= 20:
            boll_mid = closes.rolling(20).mean().iloc[-1]
            boll_std = closes.rolling(20).std().iloc[-1]
            boll_upper = boll_mid + 2 * boll_std
            boll_lower = boll_mid - 2 * boll_std
        else:
            boll_mid = boll_upper = boll_lower = None

        # 量比
        if len(volumes) >= 6:
            vol_avg5 = volumes.iloc[-6:-1].mean()
            volume_ratio = float(volumes.iloc[-1] / vol_avg5) if vol_avg5 > 0 else None
        else:
            volume_ratio = None

        trend = self._judge_trend(ma5, ma10, ma20)

        indicators = TechnicalIndicators(
            ma5=round(ma5, 2) if ma5 is not None else None,
            ma10=round(ma10, 2) if ma10 is not None else None,
            ma20=round(ma20, 2) if ma20 is not None else None,
            macd=round(macd_val, 4) if macd_val is not None else None,
            macd_signal=round(macd_signal, 4) if macd_signal is not None else None,
            macd_hist=round(macd_hist_val, 4) if macd_hist_val is not None else None,
            rsi=round(rsi_val, 2) if rsi_val is not None else None,
            boll_upper=round(boll_upper, 2) if boll_upper is not None else None,
            boll_mid=round(boll_mid, 2) if boll_mid is not None else None,
            boll_lower=round(boll_lower, 2) if boll_lower is not None else None,
            volume_ratio=round(volume_ratio, 2) if volume_ratio is not None else None,
            trend=trend,
        )

        cache.set(cache_key, indicators.model_dump(), ttl=300)
        return indicators

    def get_money_flow(self, stock_code: str) -> MoneyFlow:
        """获取个股资金流向"""
        cache_key = f"money_flow:{stock_code}"
        cached = cache.get(cache_key)
        if cached:
            return MoneyFlow(**cached)

        raw = self.repo.get_money_flow(stock_code)
        flow = MoneyFlow(**raw)
        cache.set(cache_key, flow.model_dump(), ttl=300)
        return flow

    def search_stock(self, query: str) -> list[StockSearchResult]:
        """模糊搜索股票"""
        if not query or len(query) < 1:
            return []

        cache_key = f"stock_search:{query}"
        cached = cache.get(cache_key)
        if cached:
            return [StockSearchResult(**item) for item in cached]

        raw = self.repo.search_by_name(query)
        results = [StockSearchResult(code=item["code"], name=item["name"]) for item in raw]
        cache.set(cache_key, [r.model_dump() for r in results], ttl=600)
        return results

    def get_stock_name(self, stock_code: str) -> str | None:
        """获取股票名称"""
        return self.repo.get_stock_name(stock_code)

    def get_market_data(self, days: int = 20) -> dict:
        """获取大盘指数数据（带缓存）"""
        cache_key = f"market_index:{days}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        data = self.repo.get_market_index(days)
        if data:
            cache.set(cache_key, data, ttl=600)
        return data

    # ========== 工具方法 ==========

    @staticmethod
    def _judge_trend(ma5, ma10, ma20) -> str:
        if ma5 is None or ma10 is None or ma20 is None:
            return "数据不足"
        if ma5 > ma10 > ma20:
            return "多头排列"
        elif ma5 < ma10 < ma20:
            return "空头排列"
        else:
            return "震荡"

    @staticmethod
    def _extract_number(d: dict, keys: list):
        for k in keys:
            if k in d:
                try:
                    return float(d[k])
                except (TypeError, ValueError):
                    return None
        return None
