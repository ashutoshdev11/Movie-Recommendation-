"""
Aggregated API v1 router for MovieRec Version 2.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.movies import router as movies_router
from app.api.v1.ratings import router as ratings_router
from app.api.v1.watchlist import router as watchlist_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.posters import router as posters_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(movies_router)
api_router.include_router(ratings_router)
api_router.include_router(watchlist_router)
api_router.include_router(recommendations_router)
api_router.include_router(posters_router)
