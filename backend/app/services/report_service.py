from app.core.logger import log_with_trace
from app.graph.workflow import build_graph


class ReportService:

    def __init__(self):

        self.graph = build_graph()


    async def generate_report(self, stock_code: str, question: str):

        log_with_trace(f"Start generating investment report: {stock_code}")

        result = await self.graph.ainvoke({

            "stock_code": stock_code,

            "question": question
        })

        return result