import os
import time
import akshare as ak
import pandas as pd
import requests
import requests.adapters
import requests.sessions


# ========== 代理绕过 ==========
# 国内财经 API 不应走外网代理，彻底禁用避免 ProxyError
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
           "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# Patch 1: HTTPAdapter.send — 强制清空 proxies + 超时
_orig_adapter_send = requests.adapters.HTTPAdapter.send

def _patched_adapter_send(self, request, **kwargs):
    kwargs["proxies"] = {"http": None, "https": None}
    if "timeout" not in kwargs or kwargs["timeout"] is None:
        kwargs["timeout"] = 10.0
    return _orig_adapter_send(self, request, **kwargs)

requests.adapters.HTTPAdapter.send = _patched_adapter_send

# Patch 2: Session.__init__ — 禁用 trust_env 防止从系统读代理
_orig_session_init = requests.sessions.Session.__init__

def _patched_session_init(self, *args, **kw):
    _orig_session_init(self, *args, **kw)
    self.trust_env = False
    self.proxies = {"http": None, "https": None}

requests.sessions.Session.__init__ = _patched_session_init

# Patch 3: Session.send — 双重保险
_orig_session_send = requests.sessions.Session.send

def _patched_session_send(self, request, **kwargs):
    kwargs["proxies"] = {"http": None, "https": None}
    return _orig_session_send(self, request, **kwargs)

requests.sessions.Session.send = _patched_session_send


class AkShareRepository:

    # ========== 内部工具 ==========
    
    @staticmethod
    def _fetch_hist_with_retry(symbol: str, retries: int = 3, delay: float = 1.0):
        """带重试的 K 线获取（东方财富 API 不稳定）"""
        last_err = None
        for attempt in range(retries):
            try:
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="")
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                last_err = e
                if attempt < retries - 1:
                    time.sleep(delay * (attempt + 1))
        return None
    
    def get_stock_price(self, symbol: str):
        df = self._fetch_hist_with_retry(symbol)
        if df is None or df.empty:
            return {}
        last = df.iloc[-1]
        return {
            "symbol": symbol,
            "open": float(last["\u5f00\u76d8"]),
            "close": float(last["\u6536\u76d8"]),
            "high": float(last["\u6700\u9ad8"]),
            "low": float(last["\u6700\u4f4e"]),
            "volume": float(last["\u6210\u4ea4\u91cf"]),
        }

    def get_financial(self, symbol: str) -> dict:
        """获取财务核心指标：PE、ROE、营收、市值"""
        result = {}

        # 1. PE TTM — 百度股市通（稳定可用）
        try:
            df = ak.stock_zh_valuation_baidu(
                symbol=symbol, indicator="市盈率(TTM)", period="近一年"
            )
            if df is not None and not df.empty:
                pe_val = df.iloc[-1]["value"]
                if pd.notna(pe_val) and pe_val != 0:
                    result["市盈率"] = float(pe_val)
        except Exception:
            pass

        # 2. 总市值 — 百度股市通
        try:
            df = ak.stock_zh_valuation_baidu(
                symbol=symbol, indicator="总市值", period="近一年"
            )
            if df is not None and not df.empty:
                mv = df.iloc[-1]["value"]
                if pd.notna(mv) and mv != 0:
                    result["总市值"] = float(mv)  # 单位：亿
        except Exception:
            pass

        # 3. ROE — 新浪财经财务分析指标
        try:
            import datetime
            start_year = str(datetime.datetime.now().year - 1)
            df = ak.stock_financial_analysis_indicator(
                symbol=symbol, start_year=start_year
            )
            if df is not None and not df.empty:
                row = df.iloc[0]
                # 按列位置查找「加权净资产收益率」
                cols = list(row.index)
                for col in cols:
                    if "加权" in col and "净资产收益率" in col:
                        val = row[col]
                        if pd.notna(val):
                            result["净资产收益率"] = float(val)
                        break
                # 每股收益（用于计算 EPS）
                for col in cols:
                    if "加权每股收益" in col:
                        val = row[col]
                        if pd.notna(val):
                            result["每股收益"] = float(val)
                        break
        except Exception:
            pass

        # 4. 营收 — 新浪财务摘要
        try:
            df = ak.stock_financial_abstract(symbol=symbol)
            if df is not None and not df.empty:
                row = df.iloc[0]
                for key in row.index:
                    if "营业收入" in str(key):
                        val = row[key]
                        if pd.notna(val) and val != 0:
                            result["营业收入"] = float(val)
                        break
        except Exception:
            pass

        return result

    # ========== 短线分析新增方法 ==========

    def get_hist_kline(self, symbol: str, days: int = 30) -> list[dict]:
        """获取近 N 日 K 线数据"""
        try:
            df = self._fetch_hist_with_retry(symbol)
            if df is None or df.empty:
                return []
            df = df.tail(days).reset_index(drop=True)
            result = []
            for _, row in df.iterrows():
                result.append({
                    "date": str(row.get("\u65e5\u671f", "")),
                    "open": float(row.get("\u5f00\u76d8", 0)),
                    "close": float(row.get("\u6536\u76d8", 0)),
                    "high": float(row.get("\u6700\u9ad8", 0)),
                    "low": float(row.get("\u6700\u4f4e", 0)),
                    "volume": float(row.get("\u6210\u4ea4\u91cf", 0)),
                    "turnover": float(row.get("\u6362\u624b\u7387", 0)) if "\u6362\u624b\u7387" in row.index else None,
                    "amount": float(row.get("\u6210\u4ea4\u989d", 0)) if "\u6210\u4ea4\u989d" in row.index else None,
                })
            return result
        except Exception:
            return []

    def get_stock_name(self, symbol: str) -> str | None:
        """通过股票代码获取股票名称（使用缓存的股票列表）"""
        try:
            all_stocks = self._get_all_stocks()
            for s in all_stocks:
                if s["code"] == symbol:
                    return s["name"]
            return None
        except Exception:
            return None

    # 全市场代码-名称映射缓存（进程级）
    _all_stocks_cache: list[dict] | None = None

    def _get_all_stocks(self) -> list[dict]:
        """获取全市场股票 代码+名称（轻量接口）"""
        if AkShareRepository._all_stocks_cache is not None:
            return AkShareRepository._all_stocks_cache
        try:
            df = ak.stock_info_a_code_name()
            if df is None or df.empty:
                return []
            # 过滤 ST / 退市
            df = df[~df["name"].str.contains("ST|退市|退", na=False)]
            result = [
                {"code": row["code"], "name": row["name"]}
                for _, row in df.iterrows()
            ]
            AkShareRepository._all_stocks_cache = result
            return result
        except Exception:
            return []

    def search_by_name(self, query: str) -> list[dict]:
        """通过名称/代码模糊搜索股票"""
        try:
            all_stocks = self._get_all_stocks()
            if not all_stocks:
                return []
            q = query.lower()
            matched = [
                s for s in all_stocks
                if q in s["code"].lower() or q in s["name"].lower()
            ]
            return matched[:10]
        except Exception:
            return []

    def get_money_flow(self, symbol: str) -> dict:
        """获取个股资金流向（最近一日）"""
        try:
            df = ak.stock_individual_fund_flow(stock=symbol, market="sh")
            if df is None or df.empty:
                return {}
            last = df.iloc[-1]
            return {
                "main_net_inflow": float(last.get("主力净流入-净额", 0)) if "主力净流入-净额" in last.index else None,
                "super_large_net": float(last.get("超大单净流入-净额", 0)) if "超大单净流入-净额" in last.index else None,
                "large_net": float(last.get("大单净流入-净额", 0)) if "大单净流入-净额" in last.index else None,
                "retail_net_inflow": float(last.get("散户净流入-净额", 0)) if "散户净流入-净额" in last.index else None,
            }
        except Exception:
            return {}
