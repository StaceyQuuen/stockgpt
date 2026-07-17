from app.rag.retriever import NewsRetriever
from app.core.logger import log
from app.core.config import settings
from langchain_openai import ChatOpenAI


# 股票代码到名称映射（按需扩展）
STOCK_NAMES = {
    "601127": "赛力斯",
    "600519": "贵州茅台",
    "000001": "平安银行",
    "601318": "中国平安",
    "000858": "五粮液",
}

# qwen3 推理模型可能输出的思考标签
THINK_OPEN = "<" + "think>"
THINK_CLOSE = "</" + "think>"


class NewsAgent:

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            timeout=60,
            max_tokens=1024,
        )

    def run(self, state):
        log.info("News Agent running")

        stock_code = state.get("stock_code", "")
        question = state.get("question", "")
        stock_name = STOCK_NAMES.get(stock_code, "")

        # 用"股票名 + 问题"组合查询，提高 embedding 命中率
        query = f"{stock_name} {question}".strip() if stock_name else question

        retriever = NewsRetriever()
        docs = retriever.search(query)
        news = [d.page_content for d in docs]

        news_text = "\n".join(f"- {n}" for n in news) if news else "暂无相关新闻"

        prompt = f"""你是一名资深财经新闻分析师。基于以下新闻内容进行情感与影响分析。

【股票代码】{state.get("stock_code", "未知")}
【相关新闻】
{news_text}

请严格按以下 Markdown 格式输出（每个板块下方必须填写实际分析内容，不要保留占位说明）：

## 新闻摘要
（在这里写 1-2 句话概括新闻核心内容）

## 情绪判断
（在这里三选一：利好 / 利空 / 中性）

## 影响分析
（在这里写对该股票可能产生的影响，2-3 句话）

## 置信度
（在这里三选一：高 / 中 / 低）

要求：客观、简洁、不要编造数据、用中文，不要输出思考过程。"""

        response = self.llm.invoke(prompt)
        content = response.content or ""

        # 清理 qwen3 推理模型可能输出的 <think>...</think> 思考过程
        if THINK_OPEN in content and THINK_CLOSE in content:
            pre = content.split(THINK_OPEN, 1)[0]
            post = content.split(THINK_CLOSE, 1)[1]
            content = (pre + post).strip()
        analysis = content

        return {
            "news": news,
            "news_analysis": analysis,
        }
  