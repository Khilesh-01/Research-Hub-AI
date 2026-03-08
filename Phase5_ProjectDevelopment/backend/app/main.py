from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.database.database import engine, init_db, create_tables, run_schema_migrations
from app.database import models
from app.routers import auth_router, papers_router, workspace_router, chat_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — runs on startup and shutdown."""
    logger.info("Starting ResearchHub AI...")
    init_db()
    create_tables(models.Base)
    run_schema_migrations()
    logger.info("Database startup complete.")
    yield
    logger.info("ResearchHub AI shutting down.")


app = FastAPI(
    title="ResearchHub AI",
    description="Intelligent Research Paper Management and Analysis System using Agentic AI",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(papers_router.router, prefix="/papers", tags=["Papers"])
app.include_router(workspace_router.router, prefix="/workspaces", tags=["Workspaces"])
app.include_router(chat_router.router, prefix="/chat", tags=["Chat"])


@app.get("/", tags=["Health"])
def root():
    return {"message": "ResearchHub AI API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
