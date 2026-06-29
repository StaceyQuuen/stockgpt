from app.core.logger import log
from app.services.stock_service import StockDataService
from app.rag.retriever import NewsRetriever


class _RouteResult(dict):
    """路由返回值：同时满足节点更新（需 dict）和 path_map 匹配（需匹配字符串键）"""

    def __init__(self, route: str):
        super().__init__()
        self._route = route

    def __eq__(self, other):
        return self._route == other

    def __hash__(self):
        return hash(self._route)

    def __str__(self):
        return self._route

    def __repr__(self):
        return self._route


def router_node(state):

    log.info("Router node triggered")

    question = state["question"]

    if state.get("stock_code"):

        return _RouteResult("stock_analysis")

    if "新闻" in question or "消息" in question:

        return _RouteResult("rag_analysis")

    return _RouteResult("general_analysis")




def stock_node(state):

    log.info("Stock node triggered")

    service = StockDataService()

    stock_code = state["stock_code"]

    data = service.get_stock_info(stock_code)

    return {

        **state,

        "stock_data": data.dict()

    }



def rag_node(state):

    log.info("RAG node triggered")

    retriever = NewsRetriever()

    docs = retriever.search(state["question"])

    news = [d.page_content for d in docs]

    return {

        **state,

        "news_context": news

    }


def analysis_node(state):

    log.info("Analysis node triggered")

    stock_data = state.get("stock_data")

    news = state.get("news_context")

    analysis = f"""
基于数据分析：

股票数据：{stock_data}

新闻信息：{news}

综合判断：该标的处于分析阶段（后续接LLM）
"""

    return {

        **state,

        "analysis": analysis

    }

def report_node(state):

    log.info("Report node triggered")

    return {

        **state,

        "report": state.get("analysis")
    }