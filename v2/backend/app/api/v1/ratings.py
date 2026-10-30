"""
User Rating API endpoints for MovieRec Version 2.
Strict server-side user data isolation: all operations operate exclusively on current_user.id.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import User, UserRating
from app.schemas.all_schemas import RatingCreate, RatingResponse
from app.services.recommender_service import recommender_service

router = APIRouter(prefix="/ratings", tags=["User Ratings"])


@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def submit_rating(
    req: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit or update a rating (1.0 to 5.0) for a catalog movie."""
    # Verify movie exists in catalog
    movie = recommender_service.get_movie(req.movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie ID {req.movie_id} does not exist in the catalog.",
        )

    # Check existing rating for this user
    existing = db.query(UserRating).filter(
        UserRating.user_id == current_user.id,
        UserRating.movie_id == req.movie_id,
    ).first()

    if existing:
        existing.rating = float(req.rating)
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        new_rating = UserRating(
            user_id=current_user.id,
            movie_id=req.movie_id,
            rating=float(req.rating),
        )
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        target = new_rating

    return RatingResponse(
        id=target.id,
        user_id=current_user.id,
        movie_id=target.movie_id,
        rating=target.rating,
        created_at=target.created_at,
        updated_at=target.updated_at,
        movie_title=movie.get("title"),
        movie_year=movie.get("year"),
        movie_genres=movie.get("genres", []),
    )


@router.get("/me", response_model=List[RatingResponse])
def get_my_ratings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all ratings submitted by the currently authenticated user."""
    ratings = db.query(UserRating).filter(UserRating.user_id == current_user.id).order_by(UserRating.updated_at.desc()).all()
    res = []
    for r in ratings:
        meta = recommender_service.get_movie(r.movie_id) or {}
        res.append(
            RatingResponse(
                id=r.id,
                user_id=r.user_id,
                movie_id=r.movie_id,
                rating=r.rating,
                created_at=r.created_at,
                updated_at=r.updated_at,
                movie_title=meta.get("title"),
                movie_year=meta.get("year"),
                movie_genres=meta.get("genres", []),
            )
        )
    return res


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a rating interaction for the current user."""
    existing = db.query(UserRating).filter(
        UserRating.user_id == current_user.id,
        UserRating.movie_id == movie_id,
    ).first()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating for movie ID {movie_id} not found in your profile.",
        )

    db.delete(existing)
    db.commit()
    return None
