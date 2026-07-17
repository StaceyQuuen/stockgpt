from app.core.logger import log_with_trace
from app.core.config import settings
from langchain_openai import ChatOpenAI

THINK_OPEN = "<" + "think>"
THINK_CLOSE = "</" + "think>"


class ReportAgent:

    def __init__(self):

        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            timeout=120,
            max_tokens=2048,
        )

    def run(self, state):

        log_with_trace("Report Agent generating short-term analysis report")

        stock_name = state.get("stock_name", "")
        stock_code = state.get("stock_code", "")
        stock_label = f"{stock_name}({stock_code})" if stock_name else stock_code

        short_term_analysis = state.get("short_term_analysis", "")
        assessment = state.get("short_term_assessment")

        prompt = f"""你是一名专业证券分析师，请基于以下信息生成一份短线分析报告。

=====================
股票：{stock_label}

【财务分析】
{state.get("financial_analysis", "无")}

【新闻分析】
{state.get("news_analysis", "无")}

【技术分析】
{state.get("technical_analysis", "无")}

【风险评估】
{state.get("risk_analysis", "无")}

【短线适配性评估】
{short_term_analysis}
=====================

请严格按照以下结构输出：

1. 股票概览（股票名称、代码、当前价格区间）
2. 技术面要点（2-3 句话概括核心技术信号）
3. 资金与情绪（新闻情绪 + 资金流向）
4. 风险警示（主要风险点，1-2 条）
5. 短线结论（重点：适合或不适合，核心理由）
{"6. 操作策略（入场区间、止盈/止损、仓位、持仓天数）" if assessment and assessment.get("suitable") else ""}

要求：
- 专业、客观
- 不要编造数据
- 用中文
- 简洁，总字数控制在 400 字以内
- 末尾加上：⚠️ 以上分析仅供参考，不构成投资建议
"""

        response = self.llm.invoke(prompt)
        content = response.content or ""

        # 清理 qwen3 推理模型输出的思考过程
        if THINK_OPEN in content and THINK_CLOSE in content:
            pre = content.split(THINK_OPEN, 1)[0]
            post = content.split(THINK_CLOSE, 1)[1]
            content = (pre + post).strip()

        return {
            **state,
            "final_report": content
        }
