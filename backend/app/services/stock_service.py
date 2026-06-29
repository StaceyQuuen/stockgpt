from app.services.repositories.akshare_repo import AkShareRepository
from app.services.models.stock import StockInfo, StockPrice, FinancialData


class StockDataService:

    def __init__(self):

        self.repo = AkShareRepository()


    def get_stock_info(self, stock_code: str) -> StockInfo:

        price_data = self.repo.get_stock_price(stock_code)

        financial_data = self.repo.get_financial(stock_code)

        price = StockPrice(**price_data)

        financial = FinancialData(

            roe=financial_data.get("净资产收益率(%)"),
            pe=financial_data.get("市盈率"),
            revenue=financial_data.get("营业收入")

        )

        return StockInfo(

            stock_code=stock_code,

            price=price,

            financial=financial

        )