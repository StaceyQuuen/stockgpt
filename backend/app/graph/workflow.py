from langgraph.graph import StateGraph, END

from app.graph.state import GraphState

from app.agents.financial import FinancialAgent
from app.agents.news import NewsAgent
from app.agents.technical import TechnicalAgent
from app.agents.risk import RiskAgent
from app.agents.report import ReportAgent


def build_graph():

    graph = StateGraph(GraphState)

    financial = FinancialAgent()

    news = NewsAgent()

    technical = TechnicalAgent()

    risk = RiskAgent()

    report = ReportAgent()

    # ======================
    # 注册节点
    # ======================
    graph.add_node("financial", financial.run)

    graph.add_node("news", news.run)

    graph.add_node("technical", technical.run)

    graph.add_node("risk", risk.run)

    graph.add_node("report", report.run)

    # ======================
    # 并行入口（Fan-out）
    # ======================

    graph.set_entry_point("financial")

    graph.add_edge("financial", "news")

    graph.add_edge("financial", "technical")

    graph.add_edge("financial", "risk")

    # ======================
    # 汇总（Fan-in）
    # ======================

    graph.add_edge("news", "report")

    graph.add_edge("technical", "report")

    graph.add_edge("risk", "report")

    graph.add_edge("report", END)

    return graph.compile()