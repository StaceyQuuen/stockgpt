class ReportAgent:

    def run(self, state):

        report = f"""
========== StockGPT AI Report ==========

📊 财务分析
{state.get("financial_analysis")}

📰 新闻分析
{state.get("news_analysis")}

📈 技术分析
{state.get("technical_analysis")}

⚠️ 风险分析
{state.get("risk_analysis")}

=======================================
结论：多维度分析完成（并行执行优化版）
"""

        return {

            "final_report": report
        }