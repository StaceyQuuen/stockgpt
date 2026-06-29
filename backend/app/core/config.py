from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME: str = "StockGPT"

    ENV: str = "dev"

    LOG_LEVEL: str = "INFO"

    OPENAI_API_KEY: str = ""

    CHROMA_PATH: str = "./data/chroma"


settings = Settings()