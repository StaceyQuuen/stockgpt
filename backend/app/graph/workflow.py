from langgraph.graph import StateGraph, END

from app.graph.state import GraphState

from app.agents.financial import FinancialAgent
from app.agents.news import NewsAgent
from app.agents.technical import TechnicalAgent
from app.agents.risk import RiskAgent
from app.agents.short_term import ShortTermAgent
from app.agents.report import ReportAgent
from app.core.cache import Cache

cache = Cache()

def build_graph():

    graph = StateGraph(GraphState)

    financial = FinancialAgent()

    news = NewsAgent()

    technical = TechnicalAgent()

    risk = RiskAgent()

    short_term = ShortTermAgent()

    report = ReportAgent()

    # ======================
    # 注册节点
    # ======================
    graph.add_node("financial", financial.run)

    graph.add_node("news", news.run)

    graph.add_node("technical", technical.run)

    graph.add_node("risk", risk.run)

    graph.add_node("short_term", short_term.run)

    graph.add_node("report", report.run)

    # ======================
    # 并行入口（Fan-out）
    # ======================

    graph.set_entry_point("financial")

    graph.add_edge("financial", "news")

    graph.add_edge("financial", "technical")

    graph.add_edge("financial", "risk")

    # ======================
    # 汇总（Fan-in）→ short_term → report
    # ======================

    graph.add_edge("news", "short_term")

    graph.add_edge("technical", "short_term")

    graph.add_edge("risk", "short_term")

    graph.add_edge("short_term", "report")

    graph.add_edge("report", END)

    return graph.compile()

def cached_graph_invoke(graph, input_data):

    cache_key = f"graph:{input_data['stock_code']}:{input_data['question']}"

    cached = cache.get(cache_key)

    if cached:

        return cached

    result = graph.invoke(input_data)

    cache.set(cache_key, result, ttl=300)

    return result
