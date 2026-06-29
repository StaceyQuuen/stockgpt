from app.rag.retriever import NewsRetriever
from app.core.logger import log


class NewsAgent:

    def run(self, state):

        log.info("News Agent running")

        retriever = NewsRetriever()

        docs = retriever.search(state["question"])

        news = [d.page_content for d in docs]

        analysis = f"""
新闻分析：

{news}

结论：市场情绪影响中性（后续接LLM）
"""

        return {

            "news": news,

            "news_analysis": analysis
        }