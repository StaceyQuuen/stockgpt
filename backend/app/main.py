from app.core.logger import log
from app.core.config import settings


def main():

    log.info(f"Starting {settings.APP_NAME}")

    log.info(f"Environment: {settings.ENV}")

    log.info("StockGPT backend initialized successfully")


if __name__ == "__main__":

    main()