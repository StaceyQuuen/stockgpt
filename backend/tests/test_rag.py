from app.rag.retriever import NewsRetriever


retriever = NewsRetriever()

docs = retriever.search("赛力斯利好")

for d in docs:

    print(d.page_content)

    print(d.metadata)