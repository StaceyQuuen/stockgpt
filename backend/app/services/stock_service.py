from app.services.repositories.akshare_repo import AkShareRepository
from app.services.models.stock import StockInfo, StockPrice, FinancialData
from app.core.cache import Cache
from app.core.logger import log

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


    @staticmethod

    def _extract_number(d: dict, keys: list):

        for k in keys:

            if k in d:

                try:

                    return float(d[k])

                except (TypeError, ValueError):

                    return None

        return None