import os
# 必须在导入 langchain_ollama / requests / ollama 之前设置
# 否则本地 Ollama 调用会走系统代理导致 502
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")
