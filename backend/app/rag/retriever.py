from app.rag.vector_store import VectorStore


TOP_K = 4

SCORE_THRESHOLD = 0.3


class NewsRetriever:

    def __init__(self):

        self.retriever = VectorStore().get_db().as_retriever(

            search_type="similarity_score_threshold",

            search_kwargs={

                "k": TOP_K,

                "score_threshold": SCORE_THRESHOLD,

            },

        )


    def search(self, query: str):

        return self.retriever.invoke(query)
