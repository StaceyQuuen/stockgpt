import os
import sys

from app.graph.workflow import build_graph


os.system("chcp 65001 > nul")

sys.stdout.reconfigure(encoding="utf-8")


graph = build_graph()


result = graph.invoke({

    "question": "分析赛力斯投资价值",

    "stock_code": "601127"
})


print(result["final_report"])