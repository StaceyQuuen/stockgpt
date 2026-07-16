from app.core.logger import log_with_trace
from app.core.config import settings
from langchain_ollama import ChatOllama


class ReportAgent:

    def __init__(self):

        self.llm = ChatOllama(
            model="qwen3:4b",
            base_url="http://127.0.0.1:11434",
            timeout=120,
            reasoning=False,
            num_predict=150,
        )


    def run(self, state):

        log_with_trace("Report Agent generating final investment report")

        prompt = f"""
你是一名专业证券分析师，请基于以下信息生成一份完整投资报告：

=====================
【财务分析】
{state.get("financial_analysis")}

【新闻分析】
{state.get("news_analysis")}

【技术分析】
{state.get("technical_analysis")}

【风险分析】
{state.get("risk_analysis")}
=====================

请严格按照以下结构输出：

1. 股票概览
2. 财务分析
3. 行业与新闻解读
4. 技术面分析
5. 风险提示
6. 投资结论（重点）
7. 操作建议（短期/中期）

要求：
- 专业
- 客观
- 不要编造数据
- 用中文
"""

        response = self.llm.invoke(prompt)

        return {

            **state,

            "final_report": response.content
        }