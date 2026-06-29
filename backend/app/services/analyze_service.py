from app.graph.workflow import build_graph
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.core.logger import log_with_trace


class AnalyzeService:

    def __init__(self):

        self.graph = build_graph()


    async def analyze(self, req: AnalyzeRequest) -> AnalyzeResponse:

        log_with_trace(f"Start analysis: {req.stock_code}")

        result = await self.graph.ainvoke({

            "question": req.question,

            "stock_code": req.stock_code
        })

        log_with_trace("Graph execution completed")

        return AnalyzeResponse(

            stock_code=req.stock_code,

            report=result["final_report"]
        )