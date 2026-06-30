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
        yield "📊 正在调用 LangGraph...\n"

        final_state = {}

        async for event in self.graph.astream_events(
            {"stock_code": stock_code, "question": question},
            version="v2"
        ):
            kind = event.get("event")
            name = event.get("name", "")

            if kind == "on_chain_start" and name in ("financial", "news", "technical", "risk", "report"):
                yield f"▶️ {name} 节点启动\n"
            elif kind == "on_chain_end" and name in ("financial", "news", "technical", "risk", "report"):
                output = event.get("data", {}).get("output", {}) or {}
                if isinstance(output, dict):
                    final_state.update(output)

                if name == "financial":
                    yield "💰 财务分析完成\n"
                elif name == "news":
                    yield "📰 新闻分析完成\n"
                elif name == "technical":
                    yield "📈 技术分析完成\n"
                elif name == "risk":
                    yield "⚠️ 风险分析完成\n"
                elif name == "report":
                    yield "📝 报告生成完成\n"

        yield "\n========== FINAL REPORT ==========\n"
        if final_state.get("final_report"):
            yield final_state["final_report"]
        yield f"\n[{trace_id}] 分析结束\n"
