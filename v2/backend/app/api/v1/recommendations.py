"""
Personalized Recommendation endpoints for MovieRec Version 2.
Generates recommendations using user-profile SVD latent folding-in or Popularity cold-start fallback.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import User, UserRating
from app.schemas.all_schemas import RecommendationItem, RecommendationResponse
from app.services.recommender_service import recommender_service
from app.services.poster_service import poster_service

router = APIRouter(prefix="/recommendations", tags=["Recommendations Engine"])


class AnonymousProfileRequest(BaseModel):
    ratings: Dict[int, float] = Field(..., description="Mapping of movie_id to assigned rating 1.0 to 5.0")
    n: int = Field(10, ge=1, le=50)


@router.get("/me", response_model=RecommendationResponse)
def get_recommendations_for_current_user(
    n: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate personalized recommendations for the logged-in user.
    Reads user ratings directly from the database and folds them into the 30D SVD latent space.
    If the user has < 3 ratings, automatically routes to the Bayesian Damped Popularity baseline.
    """
    ratings_records = db.query(UserRating).filter(UserRating.user_id == current_user.id).all()
    user_ratings = {r.movie_id: r.rating for r in ratings_records}

    rec_result = recommender_service.recommend_for_user_ratings(user_ratings, n=n)

    # Attach poster URLs
    items = []
    for it in rec_result["items"]:
        mid = it["movie_id"]
        meta = recommender_service.get_movie(mid) or {}
        poster = poster_service.get_movie_poster(mid, meta.get("title", it["title"]), meta.get("year", it.get("year")))
        it["poster_url"] = poster.get("poster_url")
        items.append(RecommendationItem(**it))

    return RecommendationResponse(
        user_id=current_user.id,
        strategy=rec_result["strategy"],
        is_cold_start=rec_result["is_cold_start"],
        count=len(items),
        items=items,
    )


@router.post("/anonymous", response_model=RecommendationResponse)
def get_recommendations_for_anonymous_profile(req: AnonymousProfileRequest):
    """
    Generate real-time recommendations for an unauthenticated guest session.
    Accepts on-the-fly ratings and projects into SVD latent space or popularity fallback.
    """
    rec_result = recommender_service.recommend_for_user_ratings(req.ratings, n=req.n)

    items = []
    for it in rec_result["items"]:
        mid = it["movie_id"]
        meta = recommender_service.get_movie(mid) or {}
        poster = poster_service.get_movie_poster(mid, meta.get("title", it["title"]), meta.get("year", it.get("year")))
        it["poster_url"] = poster.get("poster_url")
        items.append(RecommendationItem(**it))

    return RecommendationResponse(
        user_id=None,
        strategy=rec_result["strategy"],
        is_cold_start=rec_result["is_cold_start"],
        count=len(items),
        items=items,
    )
