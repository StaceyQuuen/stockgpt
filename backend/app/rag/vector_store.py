from langchain_chroma import Chroma
from app.rag.embedding import EmbeddingModel
from app.core.config import settings


class VectorStore:

    def __init__(self):

        self.embedding = EmbeddingModel().model

        self.db = Chroma(

            collection_name="stock_news",

            embedding_function=self.embedding,

            persist_directory=settings.CHROMA_PATH

        )


    def add_documents(self, docs):

        self.db.add_documents(docs)


    def get_db(self):

        return self.db