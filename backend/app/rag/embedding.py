import os
from functools import lru_cache


# HuggingFace 模型已本地缓存，禁用在线检查避免网络等待
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


@lru_cache(maxsize=1)
def get_embedding_model():
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
