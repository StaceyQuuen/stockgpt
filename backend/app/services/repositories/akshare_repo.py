import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    def _fetch_hist_with_retry(symbol: str, retries: int = 5, delay: float = 2.0):
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
    
    @staticmethod
    def _code_to_sina_symbol(symbol: str) -> str:
        """将纯代码转为新浪格式：sh601939 / sz000001"""
        s = symbol.strip()
        if s.startswith(("sh", "sz", "SH", "SZ")):
            return s.lower()
        if s.startswith(("6", "9")):
            return f"sh{s}"
        return f"sz{s}"

    def _fetch_hist_sina(self, symbol: str) -> pd.DataFrame | None:
        """Sina 源 K 线备选（当东方财富不可用时）"""
        try:
            sina_sym = self._code_to_sina_symbol(symbol)
            df = ak.stock_zh_a_daily(symbol=sina_sym, adjust="")
            if df is not None and not df.empty:
                # 统一列名为中文，与东方财富兼容
                col_map = {
                    "date": "日期", "open": "开盘", "high": "最高",
                    "low": "最低", "close": "收盘", "volume": "成交量",
                    "amount": "成交额", "turnover": "换手率",
                }
                df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
                return df
        except Exception:
            pass
        return None

    def get_stock_price(self, symbol: str):
        df = self._fetch_hist_with_retry(symbol)
        if df is None or df.empty:
            df = self._fetch_hist_sina(symbol)
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
        """获取近 N 日 K 线数据（东方财富 → Sina 自动降级）"""
        df = self._fetch_hist_with_retry(symbol)
        if df is None or df.empty:
            df = self._fetch_hist_sina(symbol)
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

    def get_all_spot_data(self) -> pd.DataFrame | None:
        """获取全 A 股实时快照（优先 Sina，备选东方财富）"""
        # 尝试东方财富
        try:
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                return df
        except Exception:
            pass
        # 回退到 Sina 批量行情
        return self._batch_sina_spot()

    def _batch_sina_spot(self) -> pd.DataFrame | None:
        """通过 Sina hq API 批量获取实时行情"""
        import urllib.request
        all_stocks = self._get_all_stocks()
        if not all_stocks:
            return None

        # 转为 Sina 格式代码
        sina_codes = []
        code_name = {}
        for s in all_stocks:
            sc = self._code_to_sina_symbol(s["code"])
            sina_codes.append(sc)
            code_name[sc] = {"code": s["code"], "name": s["name"]}

        # 分批请求（每批 80 只）
        batch_size = 80
        rows = []
        for i in range(0, len(sina_codes), batch_size):
            batch = sina_codes[i:i + batch_size]
            codes_str = ",".join(batch)
            try:
                req = urllib.request.Request(
                    f"https://hq.sinajs.cn/list={codes_str}",
                    headers={"Referer": "https://finance.sina.com.cn"},
                )
                resp = urllib.request.urlopen(req, timeout=15)
                data = resp.read().decode("gbk")
                for line in data.strip().split("\n"):
                    row = self._parse_sina_line(line, code_name)
                    if row:
                        rows.append(row)
            except Exception:
                continue

        if not rows:
            return None
        return pd.DataFrame(rows)

    @staticmethod
    def _parse_sina_line(line: str, code_name: dict) -> dict | None:
        """解析单行 Sina 行情数据"""
        try:
            if '=""' in line or "=" not in line:
                return None
            # var hq_str_sh600519="..."
            code_part = line.split('"')[0]  # var hq_str_sh600519=
            sina_code = code_part.split("=")[0].split("_")[-1]  # sh600519
            pure_code = sina_code[2:]  # 600519

            vals = line.split('"')[1].split(",")
            if len(vals) < 32:
                return None

            name = vals[0]
            today_open = float(vals[1]) if vals[1] else 0
            yesterday_close = float(vals[2]) if vals[2] else 0
            current = float(vals[3]) if vals[3] else 0
            high = float(vals[4]) if vals[4] else 0
            low = float(vals[5]) if vals[5] else 0
            volume = float(vals[8]) if vals[8] else 0  # 股
            amount = float(vals[9]) if vals[9] else 0  # 元

            if current <= 0 or yesterday_close <= 0:
                return None

            change_pct = round((current / yesterday_close - 1) * 100, 2)
            # 换手率无法从 Sina 直接获取，用成交额估算（后续 K 线补充）

            info = code_name.get(sina_code, {})
            return {
                "代码": info.get("code", pure_code),
                "名称": info.get("name", name),
                "最新价": current,
                "涨跌幅": change_pct,
                "成交量": volume,
                "成交额": amount,
                "最高": high,
                "最低": low,
                "换手率": 0,  # Sina 不提供，后续由 K 线数据补充
            }
        except Exception:
            return None

    def _fetch_single_kline_sina(self, symbol: str, days: int) -> tuple[str, pd.DataFrame | None]:
        """单只股票 Sina K 线（线程安全）"""
        try:
            sina_sym = self._code_to_sina_symbol(symbol)
            df = ak.stock_zh_a_daily(symbol=sina_sym, adjust="")
            if df is not None and not df.empty:
                col_map = {
                    "date": "日期", "open": "开盘", "high": "最高",
                    "low": "最低", "close": "收盘", "volume": "成交量",
                    "amount": "成交额", "turnover": "换手率",
                }
                df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
                df = df.tail(days).reset_index(drop=True)
                return symbol, df
        except Exception:
            pass
        return symbol, None

    def batch_get_kline_sina(
        self, symbols: list[str], days: int = 30, max_workers: int = 8
    ) -> dict[str, pd.DataFrame]:
        """并发获取多只股票 K 线（仅 Sina 源）"""
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self._fetch_single_kline_sina, sym, days): sym
                for sym in symbols
            }
            for future in as_completed(future_map):
                try:
                    sym, df = future.result(timeout=15)
                    if df is not None and not df.empty:
                        results[sym] = df
                except Exception:
                    pass
        return results

    def get_market_index(self, days: int = 20) -> dict:
        """获取大盘指数数据（上证指数）"""
        try:
            df = ak.stock_zh_index_daily(symbol="sh000001")
            if df is None or df.empty:
                return {}
            df = df.tail(days).reset_index(drop=True)
            closes = df["close"].tolist()
            volumes = df["volume"].tolist()

            # 均线
            ma5 = sum(closes[-5:]) / min(5, len(closes[-5:])) if len(closes) >= 5 else None
            ma10 = sum(closes[-10:]) / min(10, len(closes[-10:])) if len(closes) >= 10 else None
            ma20 = sum(closes) / len(closes) if len(closes) >= 1 else None

            # 涨跌幅
            return_5d = (closes[-1] / closes[-6] - 1) * 100 if len(closes) >= 6 else None
            return_20d = (closes[-1] / closes[0] - 1) * 100 if len(closes) >= 2 else None

            # 成交量趋势
            vol_recent = volumes[-5:] if len(volumes) >= 5 else volumes
            vol_prev = volumes[-10:-5] if len(volumes) >= 10 else volumes[:5]
            vol_ratio = (sum(vol_recent) / len(vol_recent)) / (sum(vol_prev) / len(vol_prev)) if vol_prev and sum(vol_prev) > 0 else None

            return {
                "latest_close": float(closes[-1]),
                "latest_date": str(df.iloc[-1]["date"]),
                "ma5": round(ma5, 2) if ma5 else None,
                "ma10": round(ma10, 2) if ma10 else None,
                "ma20": round(ma20, 2) if ma20 else None,
                "return_5d": round(return_5d, 2) if return_5d else None,
                "return_20d": round(return_20d, 2) if return_20d else None,
                "volume_ratio": round(vol_ratio, 2) if vol_ratio else None,
            }
        except Exception:
            return {}
