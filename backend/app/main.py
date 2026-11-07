from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
except ImportError:
    RateLimitExceeded = None
    _rate_limit_exceeded_handler = None

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.rate_limit import limiter

app = FastAPI(title=settings.APP_NAME)
if hasattr(app.state, "limiter"):
    app.state.limiter = limiter
if _rate_limit_exceeded_handler and RateLimitExceeded:
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def on_startup():
    init_db()
    from app.core.database import SessionLocal
    from app.services.workflow_service import recover_orphaned_jobs
    db = SessionLocal()
    try:
        recover_orphaned_jobs(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "status": "ok", "llm_provider": settings.LLM_PROVIDER}


@app.get("/health")
def health():
    return {"status": "ok"}
