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

    graph.add_node("financial", financial.run)

    graph.add_node("news", news.run)

    graph.add_node("technical", technical.run)

    graph.add_node("risk", risk.run)

    graph.add_node("report", report.run)

    graph.set_entry_point("financial")

    graph.add_edge("financial", "news")

    graph.add_edge("news", "technical")

    graph.add_edge("technical", "risk")

    graph.add_edge("risk", "report")

    graph.add_edge("report", END)

    return graph.compile()