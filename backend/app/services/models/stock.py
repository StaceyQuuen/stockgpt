from pydantic import BaseModel


class StockPrice(BaseModel):

    symbol: str

    close: float

    open: float

    high: float

    low: float

    volume: float


class FinancialData(BaseModel):

    roe: float | None = None

    pe: float | None = None

    revenue: float | None = None


class StockInfo(BaseModel):

    stock_code: str

    price: StockPrice

    financial: FinancialData