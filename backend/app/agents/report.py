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
            max_tokens=3072,
        )

    def run(self, state):

        log_with_trace("Report Agent generating short-term analysis report")

        stock_name = state.get("stock_name", "")
        stock_code = state.get("stock_code", "")
        stock_label = f"{stock_name}({stock_code})" if stock_name else stock_code

        short_term_analysis = state.get("short_term_analysis", "")
        assessment = state.get("short_term_assessment")

        # 判断是否适合短线（决定是否输出买点/风险/卖点/仓位）
        is_suitable = False
        if assessment and isinstance(assessment, dict):
            is_suitable = bool(assessment.get("suitable", False))

        # 根据短线评分决定输出结构
        if is_suitable:
            output_structure = """请严格按照以下 10 项结构输出分析报告：

1. 大盘环境（大盘强弱、是否有利于短线操作）
2. 板块强度（根据"{stock_name}"推断所属板块，分析该板块近期是否有资金关注）
3. 个股趋势（直接回答：是否处于上升趋势）
4. 位置（直接回答：低位、突破、回踩还是高位）
5. 量价关系（直接回答：放量突破、缩量回调、放量下跌等）
6. 主力行为（基于量价模式推断吸筹/洗盘/拉升/派发阶段）
7. 买点分析（是否满足买入条件：均线支撑、缩量企稳、RSI 等）
8. 风险控制（止损位设定、最大回撤风险、主要风险点）
9. 卖点规划（止盈目标、压力位、RSI 超买等卖出信号）
10. 仓位管理（具体仓位建议：单只股票不要满仓，确定性一般时先用30%~50%仓位试探）"""
            word_limit = 600
        else:
            output_structure = """请严格按照以下 6 项结构输出分析报告（该股票当前不适合短线，无需输出买卖点和仓位）：

1. 大盘环境（大盘强弱、是否有利于短线操作）
2. 板块强度（根据"{stock_name}"推断所属板块，分析该板块近期是否有资金关注）
3. 个股趋势（直接回答：是否处于上升趋势）
4. 位置（直接回答：低位、突破、回踩还是高位）
5. 量价关系（直接回答：放量突破、缩量回调、放量下跌等）
6. 主力行为（基于量价模式推断吸筹/洗盘/拉升/派发阶段）

最后追加一句结论：该股票当前不适合短线操作，并简要说明原因。"""
            word_limit = 400

        prompt = f"""你是一名专业证券分析师，请基于以下信息生成一份短线分析报告。

=====================
股票：{stock_label}

【大盘环境】
{state.get("market_analysis", "无")}

【财务分析】
{state.get("financial_analysis", "无")}

【新闻分析】
{state.get("news_analysis", "无")}

【技术分析（含位置、量价、主力行为）】
{state.get("technical_analysis", "无")}

【风险评估（含买卖点、仓位建议）】
{state.get("risk_analysis", "无")}

【短线适配性评估】
{short_term_analysis}
=====================

{output_structure}

要求：
- 专业、客观，基于数据说话
- 不要编造数据，没有的数据标注"数据不足"
- 用中文
- 简洁，总字数控制在 {word_limit} 字以内
- 末尾加上：⚠️ 以上分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。
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
