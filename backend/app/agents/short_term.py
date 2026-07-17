import json
import re

from app.core.logger import log_with_trace
from app.core.config import settings
from langchain_openai import ChatOpenAI

# qwen3 推理模型可能输出的思考标签
THINK_OPEN = "<" + "think>"
THINK_CLOSE = "</" + "think>"


class ShortTermAgent:
    """
    短线适配性评估 Agent
    汇总技术面、资金面、风险面、新闻情绪，通过 LLM 判断是否适合短线操作
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            timeout=120,
            max_tokens=2048,
        )

    def run(self, state):
        log_with_trace("ShortTerm Agent running - 评估短线适配性")

        stock_code = state.get("stock_code", "")
        financial_analysis = state.get("financial_analysis", "无")
        news_analysis = state.get("news_analysis", "无")
        technical_analysis = state.get("technical_analysis", "无")
        risk_analysis = state.get("risk_analysis", "无")

        # 数据不足兆底：如果技术指标全为 None，直接返回数据不足
        indicators = state.get("indicators")
        risk_data = state.get("risk")
        if (not indicators or indicators.get("ma5") is None) and \
           (not risk_data or risk_data.get("annual_volatility") is None):
            log_with_trace("ShortTermAgent: 数据不足，跳过 LLM 评估")
            assessment = {
                "suitable": False,
                "score": 0,
                "reasons": [
                    "无法获取该股票的交易数据（可能为非交易日或停牌）",
                    "技术指标无法计算，缺少 K 线数据",
                    "建议在下个交易日重新分析",
                ],
                "strategy": None,
            }
            return self._build_result(assessment)

        prompt = f"""你是一名资深短线交易分析师。请基于以下数据，评估该股票是否适合短线操作。

【股票代码】{stock_code}

【财务分析】
{financial_analysis}

【新闻分析】
{news_analysis}

【技术分析】
{technical_analysis}

【风险评估】
{risk_analysis}

请严格按照以下 JSON 格式输出，不要输出其他内容，不要输出思考过程：

{{
  "suitable": true 或 false,
  "score": 0-100 之间的整数（综合评分，60分以上为适合），
  "reasons": ["原因1", "原因2", "原因3"],
  "strategy": {{
    "entry_range": "建议入场价格区间，如 15.2-15.5",
    "stop_profit": "止盈位及涨幅，如 16.8 (+8%)",
    "stop_loss": "止损位及跌幅，如 14.6 (-4%)",
    "position_ratio": "建议仓位比例，如 30%",
    "hold_days": "预期持仓天数，如 3-5个交易日"
  }}
}}

评分维度（满分 100）：
- 技术面（40分）：均线趋势、MACD、RSI、布林带位置
- 波动/流动性（25分）：年化波动率、换手率、日均成交额
- 资金面（20分）：主力资金流向（如有）
- 新闻情绪（15分）：利好/利空/中性

要求：
- 如果 suitable 为 false，strategy 填 null
- reasons 至少写 3 条，每条不超过 50 字
- 不要编造数据，基于给出的分析结果判断
- 只输出 JSON，不要有额外文字
"""

        response = self.llm.invoke(prompt)
        content = response.content or ""

        # 清理 <think> 标签
        if THINK_OPEN in content and THINK_CLOSE in content:
            pre = content.split(THINK_OPEN, 1)[0]
            post = content.split(THINK_CLOSE, 1)[1]
            content = (pre + post).strip()

        # 解析 JSON（容错处理）
        assessment = self._parse_assessment(content, state)
        return self._build_result(assessment)

    def _build_result(self, assessment: dict) -> dict:
        """构建评估结果和分析文本"""
        # 构建分析文本
        if assessment["suitable"]:
            verdict = "✅ 适合短线操作"
            strategy = assessment.get("strategy", {})
            strategy_text = f"""
【持仓策略】
- 入场区间：{strategy.get('entry_range', '待定')}
- 止盈位：{strategy.get('stop_profit', '待定')}
- 止损位：{strategy.get('stop_loss', '待定')}
- 建议仓位：{strategy.get('position_ratio', '待定')}
- 预期持仓：{strategy.get('hold_days', '待定')}
""" if strategy else "\n策略数据解析异常\n"
        else:
            verdict = "❌ 不适合短线操作"
            strategy_text = "\n建议观望或等待更好的入场时机。\n"

        reasons_text = "\n".join(f"  • {r}" for r in assessment.get("reasons", []))

        analysis = f"""
========== 短线适配性评估 ==========

【综合评分】{assessment.get('score', 0)} / 100
【判定结果】{verdict}

【判断依据】
{reasons_text}
{strategy_text}
⚠️ 以上分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。
"""

        return {
            "short_term_assessment": assessment,
            "short_term_analysis": analysis,
        }

    def _parse_assessment(self, content: str, state: dict) -> dict:
        """解析 LLM 输出的 JSON，带容错"""
        default = {
            "suitable": False,
            "score": 0,
            "reasons": ["LLM 输出解析失败，无法给出评估"],
            "strategy": None,
        }

        if not content:
            return default

        # 尝试从文本中提取 JSON 块
        json_match = re.search(r"\{[\s\S]*\}", content)
        if not json_match:
            log_with_trace(f"ShortTermAgent: 无法提取 JSON，原始内容：{content[:200]}")
            return default

        try:
            data = json.loads(json_match.group())

            # 校验必要字段
            suitable = bool(data.get("suitable", False))
            score = float(data.get("score", 0))
            reasons = data.get("reasons", [])
            strategy = data.get("strategy", None)

            if not isinstance(reasons, list):
                reasons = [str(reasons)]

            # score 范围限制
            score = max(0, min(100, score))

            return {
                "suitable": suitable,
                "score": score,
                "reasons": reasons,
                "strategy": strategy,
            }
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            log_with_trace(f"ShortTermAgent: JSON 解析失败：{e}")
            return default
