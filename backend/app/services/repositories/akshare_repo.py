import akshare as ak
import pandas as pd


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