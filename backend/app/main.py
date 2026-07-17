from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes.short_term import router as short_term_router

from app.core.trace import generate_trace_id, set_trace_id
from app.core.logger import log


app = FastAPI(title="StockGPT", version="0.1.0")


# =========================
# CORS Middleware
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Trace Middleware
# =========================
@app.middleware("http")
async def trace_middleware(request: Request, call_next):

    trace_id = generate_trace_id()

    set_trace_id(trace_id)

    log.info(f"[{trace_id}] Request started: {request.url}")

    response = await call_next(request)

    response.headers["X-Trace-Id"] = trace_id

    log.info(f"[{trace_id}] Request finished")

    return response


app.include_router(short_term_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
