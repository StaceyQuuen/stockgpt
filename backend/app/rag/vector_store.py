from langchain_chroma import Chroma
from app.rag.embedding import get_embedding_model
from app.core.config import settings


class VectorStore:

    _instance = None
    _db = None

    def __init__(self):
        if VectorStore._instance is None:
            VectorStore._instance = self
            VectorStore._db = Chroma(
                collection_name="stock_news",
                embedding_function=get_embedding_model(),
                persist_directory=settings.CHROMA_PATH
            )
        self.db = VectorStore._db

    def add_documents(self, docs):
        self.db.add_documents(docs)

    def get_db(self):
        return self.db
