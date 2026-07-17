import asyncio
from app.graph.workflow import build_graph
from app.core.trace import get_trace_id
from app.core.logger import log_with_trace
from app.services.stock_service import StockDataService


class ShortTermStreamService:
    """短线分析流式服务"""

    def __init__(self):
        self.graph = build_graph()

    async def stream(self, stock_code: str, question: str):
        trace_id = get_trace_id()

        # 获取股票名称
        stock_name = ""
        try:
            svc = StockDataService()
            stock_name = svc.get_stock_name(stock_code) or ""
        except Exception:
            pass

        label = f"{stock_name}({stock_code})" if stock_name else stock_code

        yield f"[{trace_id}] 开始短线分析 {label}\n"
        yield "📊 正在调用 LangGraph...\n"

        final_state = {}

        input_data = {
            "stock_code": stock_code,
            "question": question,
            "stock_name": stock_name,
        }

        async for event in self.graph.astream_events(
            input_data,
            version="v2"
        ):
            kind = event.get("event")
            name = event.get("name", "")

            if kind == "on_chain_start" and name in (
                "financial", "news", "technical", "risk", "short_term", "report"
            ):
                yield f"▶️ {name} 节点启动\n"

            elif kind == "on_chain_end" and name in (
                "financial", "news", "technical", "risk", "short_term", "report"
            ):
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
                elif name == "short_term":
                    yield "🎯 短线评估完成\n"
                elif name == "report":
                    yield "📝 报告生成完成\n"

        # 输出短线评估结果
        assessment = final_state.get("short_term_assessment")
        if assessment:
            yield "\n========== SHORT-TERM ASSESSMENT ==========\n"
            yield f"评分: {assessment.get('score', 0)}/100\n"
            yield f"适合短线: {'✅ 是' if assessment.get('suitable') else '❌ 否'}\n"
            reasons = assessment.get("reasons", [])
            for r in reasons:
                yield f"  • {r}\n"

            strategy = assessment.get("strategy")
            if strategy and assessment.get("suitable"):
                yield "\n【持仓策略】\n"
                yield f"  入场区间: {strategy.get('entry_range', '待定')}\n"
                yield f"  止盈位: {strategy.get('stop_profit', '待定')}\n"
                yield f"  止损位: {strategy.get('stop_loss', '待定')}\n"
                yield f"  建议仓位: {strategy.get('position_ratio', '待定')}\n"
                yield f"  预期持仓: {strategy.get('hold_days', '待定')}\n"

        # 输出完整报告
        yield "\n========== FINAL REPORT ==========\n"
        if final_state.get("final_report"):
            yield final_state["final_report"]
        yield f"\n[{trace_id}] 分析结束\n"
        yield "\n⚠️ 以上分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。\n"
