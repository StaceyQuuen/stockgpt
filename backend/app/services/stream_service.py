import asyncio
from app.graph.workflow import build_graph
from app.core.trace import get_trace_id
from app.core.logger import log_with_trace


class StreamAnalyzeService:

    def __init__(self):

        self.graph = build_graph()


    async def stream(self, stock_code: str, question: str):

        trace_id = get_trace_id()

        yield f"[{trace_id}] 开始分析 {stock_code}\n"

        await asyncio.sleep(0.5)

        yield "📊 正在调用 LangGraph...\n"

        result = await self.graph.ainvoke({

            "stock_code": stock_code,

            "question": question
        })

        yield "📈 财务分析完成\n"

        await asyncio.sleep(0.3)

        yield "📰 新闻分析完成\n"

        await asyncio.sleep(0.3)

        yield "⚠️ 风险分析完成\n"

        await asyncio.sleep(0.3)

        yield "\n========== FINAL REPORT ==========\n"

        yield result["final_report"]

        yield f"\n[{trace_id}] 分析结束\n"