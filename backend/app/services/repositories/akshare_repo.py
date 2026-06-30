import os
import akshare as ak
import pandas as pd
import requests.adapters


# 国内财经 API 不应走外网代理，清空避免 ProxyError
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(_k, None)
os.environ["NO_PROXY"] = "*"


# 给 akshare 内部 requests 设置超时和禁用重试，避免卡死
_orig_send = requests.adapters.HTTPAdapter.send


def _patched_send(self, request, **kwargs):
    if "timeout" not in kwargs or kwargs["timeout"] is None:
        kwargs["timeout"] = 3.0
    kwargs["proxies"] = {"http": None, "https": None}
    return _orig_send(self, request, **kwargs)


requests.adapters.HTTPAdapter.send = _patched_send


class AkShareRepository:

    def get_stock_price(self, symbol: str):
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="")
        last = df.iloc[-1]
        return {
            "symbol": symbol,
            "open": float(last["开盘"]),
            "close": float(last["收盘"]),
            "high": float(last["最高"]),
            "low": float(last["最低"]),
            "volume": float(last["成交量"]),
        }


    def get_financial(self, symbol: str):
        try:
            df = ak.stock_financial_abstract(symbol=symbol)
            if df is None or df.empty:
                return {}
            return df.iloc[0].to_dict()
        except Exception:
            return {}