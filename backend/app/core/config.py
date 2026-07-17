from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    APP_NAME: str = "StockGPT"

    ENV: str = "dev"

    LOG_LEVEL: str = "INFO"

    OPENAI_API_KEY: str = ""

    LLM_BASE_URL: str = "http://tokenhub.ss.gofund.cn/v1"

    LLM_MODEL: str = "tp_anthropic.deepseek-v4-pro"

    CHROMA_PATH: str = "./data/chroma"


settings = Settings()
