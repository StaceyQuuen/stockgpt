from app.core.logger import log


class RiskAgent:

    def run(self, state):

        log.info("Risk Agent running")

        risk = {
            "market_risk": "medium",
            "volatility": "unknown",
            "liquidity": "normal"
        }

        analysis = """
风险分析：

市场风险：中等
波动率：未知
流动性：正常

结论：风险可控
"""

        return {

            "risk": risk,

            "risk_analysis": analysis
        }