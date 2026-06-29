from app.rag.loader import NewsLoader
from app.rag.splitter import TextSplitter
from app.rag.vector_store import VectorStore


def build():

    loader = NewsLoader()

    splitter = TextSplitter()

    vs = VectorStore()

    docs = loader.load("app/data/news/sample.json")

    chunks = splitter.split(docs)

    vs.add_documents(chunks)

    print(f"Indexed {len(chunks)} chunks")


if __name__ == "__main__":

    build()