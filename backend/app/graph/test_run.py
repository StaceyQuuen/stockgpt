from app.graph.workflow import build_graph


graph = build_graph()


result = graph.invoke({

    "question": "分析赛力斯投资价值",

    "stock_code": "601127"
})


print(result["final_report"])