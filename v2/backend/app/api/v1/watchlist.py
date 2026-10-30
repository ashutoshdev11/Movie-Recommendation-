"""
User Watchlist API endpoints for MovieRec Version 2.
Enforces strict user isolation: each user manages only their own watchlist items.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import User, WatchlistItem
from app.schemas.all_schemas import WatchlistAdd, WatchlistResponse
from app.services.recommender_service import recommender_service
from app.services.poster_service import poster_service

router = APIRouter(prefix="/watchlist", tags=["User Watchlist"])


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    req: WatchlistAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a movie to the authenticated user's watchlist."""
    movie = recommender_service.get_movie(req.movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie ID {req.movie_id} does not exist in catalog.",
        )

    # Check if already in watchlist
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.movie_id == req.movie_id,
    ).first()

    if existing:
        target = existing
    else:
        new_item = WatchlistItem(user_id=current_user.id, movie_id=req.movie_id)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        target = new_item

    poster = poster_service.get_movie_poster(target.movie_id, movie["title"], movie.get("year"))
    return WatchlistResponse(
        id=target.id,
        user_id=current_user.id,
        movie_id=target.movie_id,
        added_at=target.added_at,
        movie_title=movie.get("title"),
        movie_year=movie.get("year"),
        movie_genres=movie.get("genres", []),
        poster_url=poster.get("poster_url"),
    )


@router.get("/me", response_model=List[WatchlistResponse])
def get_my_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all movies saved in the current user's personal watchlist."""
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == current_user.id).order_by(WatchlistItem.added_at.desc()).all()
    res = []
    for item in items:
        meta = recommender_service.get_movie(item.movie_id) or {}
        poster = poster_service.get_movie_poster(item.movie_id, meta.get("title", ""), meta.get("year"))
        res.append(
            WatchlistResponse(
                id=item.id,
                user_id=item.user_id,
                movie_id=item.movie_id,
                added_at=item.added_at,
                movie_title=meta.get("title"),
                movie_year=meta.get("year"),
                movie_genres=meta.get("genres", []),
                poster_url=poster.get("poster_url"),
            )
        )
    return res


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a movie from the current user's watchlist."""
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.movie_id == movie_id,
    ).first()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie ID {movie_id} is not in your watchlist.",
        )

    db.delete(existing)
    db.commit()
    return None
