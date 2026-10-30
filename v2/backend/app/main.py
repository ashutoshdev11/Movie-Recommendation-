"""
Main FastAPI Application Entrypoint for MovieRec Version 2.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine


# Initialize database tables on import
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Next-Generation Collaborative Filtering Movie Discovery Engine powered by MovieLens 1M.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for React frontend (supports credentials for HTTP-only cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def health_check():
    """Service health and readiness probe."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": "standalone_v2",
        "dataset": "MovieLens 1M",
        "champion_model": "TruncatedSVD(k=30)",
    }


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Welcome to MovieRec Version 2 API. Explore interactive docs at /docs",
    }
