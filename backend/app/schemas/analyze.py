from pydantic import BaseModel


class AnalyzeRequest(BaseModel):

    stock_code: str

    question: str


class AnalyzeResponse(BaseModel):

    stock_code: str

    report: str