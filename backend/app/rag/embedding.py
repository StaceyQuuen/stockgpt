from langchain_community.embeddings import HuggingFaceEmbeddings


class EmbeddingModel:

    def __init__(self):

        self.model = HuggingFaceEmbeddings(

            model_name="BAAI/bge-small-zh-v1.5"

        )