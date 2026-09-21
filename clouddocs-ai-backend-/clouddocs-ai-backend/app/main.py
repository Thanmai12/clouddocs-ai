from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, engine
from app.routers import documents, chat

# Creates tables on startup if they don't exist yet (fine for a portfolio project;
# use Alembic migrations for anything beyond that).
Base.metadata.create_all(bind=engine)

# Basic per-IP rate limiting so a script can't burn through the free-tier
# Groq/Supabase/Render quotas by hammering the API in a loop. Not a
# substitute for real auth, but a reasonable guard for a public demo.
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="CloudDocs AI",
    description="Event-driven document Q&A platform — upload a document, "
                 "it's processed and indexed in the background, then ask questions "
                 "and get answers grounded in the source text with citations.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "CloudDocs AI"}

