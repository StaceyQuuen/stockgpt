from app.core.logger import log


class ReportAgent:

    def run(self, state):

        log.info("Report Agent running")

        report = f"""
========= StockGPT 分析报告 =========

【财务】
{state.get('financial_analysis')}

【新闻】
{state.get('news_analysis')}

【技术】
{state.get('technical_analysis')}

【风险】
{state.get('risk_analysis')}

====================================
"""

        return {
            **state,
            "final_report": report
        }