from fastapi import FastAPI

from app.api.v1.routes.analyze import router as analyze_router

from app.core.logger import log
from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0"
)


app.include_router(
    analyze_router,
    prefix="/api/v1"
)


@app.on_event("startup")
def startup():

    log.info(f"{settings.APP_NAME} API started")


@app.get("/health")
def health():

    return {"status": "ok"}