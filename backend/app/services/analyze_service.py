from app.graph.workflow import build_graph
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.core.logger import log_with_trace
from app.graph.workflow import build_graph
from app.graph.workflow import cached_graph_invoke

class AnalyzeService:

    def __init__(self):

        self.graph = build_graph()


    async def analyze(self, req: AnalyzeRequest) -> AnalyzeResponse:

        result = cached_graph_invoke(

            self.graph,

            {

                "stock_code": req.stock_code,

                "question": req.question
            }
        )

        return result