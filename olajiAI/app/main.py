# main.py (updated)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging, log
from app.routers import chats
from app.core.database import create_tables

setup_logging()

# Initialize database tables
create_tables()

app = FastAPI(title="SchoolOps AI Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_trace(request: Request, call_next):
    import uuid, time
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    start = time.time()
    response = await call_next(request)
    took = int((time.time() - start) * 1000)
    log.info("request", path=str(request.url), method=request.method, status=response.status_code, took_ms=took, trace_id=trace_id)
    response.headers["X-Trace-Id"] = trace_id
    return response

@app.get("/healthz")
async def healthz():
    return {"ok": True}

app.include_router(chats.router)