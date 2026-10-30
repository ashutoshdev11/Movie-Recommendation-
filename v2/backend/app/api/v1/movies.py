"""
Movie catalog and discovery endpoints for MovieRec Version 2.
Search, genres, details, trending, top-rated, and latent factor item similarity.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.ml.dataset import ML_1M_GENRES
from app.schemas.all_schemas import MovieDetails, MovieSummary, PaginatedMovies
from app.services.recommender_service import recommender_service
from app.services.poster_service import poster_service

router = APIRouter(prefix="/movies", tags=["Movies Catalog"])


@router.get("", response_model=PaginatedMovies)
def search_movies(
    q: Optional[str] = Query(None, description="Search query for movie title"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Search catalog movies by title and/or genre with pagination."""
    offset = (page - 1) * limit
    items, total = recommender_service.search_movies(query=q, genre=genre, limit=limit, offset=offset)

    movie_summaries = []
    for item in items:
        mid = item["movie_id"]
        poster_info = poster_service.get_movie_poster(mid, item["title"], item.get("year"))
        movie_summaries.append(
            MovieSummary(
                movie_id=mid,
                title=item["title"],
                year=item.get("year"),
                genres=item.get("genres", []),
                avg_rating=round(float(item.get("avg_rating", 0.0)), 2),
                rating_count=int(item.get("rating_count", 0)),
                poster_url=poster_info.get("poster_url"),
            )
        )

    return PaginatedMovies(
        total=total,
        page=page,
        limit=limit,
        items=movie_summaries,
    )


@router.get("/genres", response_model=List[str])
def list_genres():
    """List all available MovieLens 1M genres."""
    return ML_1M_GENRES


@router.get("/trending", response_model=List[MovieSummary])
def get_trending(limit: int = Query(12, ge=1, le=50)):
    """Fetch top trending catalog titles by historical rating engagement."""
    movies = recommender_service.get_trending(limit=limit)
    res = []
    for m in movies:
        mid = m["movie_id"]
        poster = poster_service.get_movie_poster(mid, m["title"], m.get("year"))
        res.append(
            MovieSummary(
                movie_id=mid,
                title=m["title"],
                year=m.get("year"),
                genres=m.get("genres", []),
                avg_rating=round(float(m.get("avg_rating", 0.0)), 2),
                rating_count=int(m.get("rating_count", 0)),
                poster_url=poster.get("poster_url"),
            )
        )
    return res


@router.get("/top-rated", response_model=List[MovieSummary])
def get_top_rated(limit: int = Query(12, ge=1, le=50)):
    """Fetch top critically acclaimed movies by Bayesian damped average rating."""
    movies = recommender_service.get_top_rated(limit=limit)
    res = []
    for m in movies:
        mid = m["movie_id"]
        poster = poster_service.get_movie_poster(mid, m["title"], m.get("year"))
        res.append(
            MovieSummary(
                movie_id=mid,
                title=m["title"],
                year=m.get("year"),
                genres=m.get("genres", []),
                avg_rating=round(float(m.get("avg_rating", 0.0)), 2),
                rating_count=int(m.get("rating_count", 0)),
                poster_url=poster.get("poster_url"),
            )
        )
    return res


@router.get("/{movie_id}", response_model=MovieDetails)
def get_movie_details(movie_id: int):
    """Retrieve metadata and artwork for a specific movie ID."""
    movie = recommender_service.get_movie(movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found in catalog.",
        )

    poster = poster_service.get_movie_poster(movie_id, movie["title"], movie.get("year"))
    return MovieDetails(
        movie_id=movie_id,
        title=movie["title"],
        year=movie.get("year"),
        genres=movie.get("genres", []),
        avg_rating=round(float(movie.get("avg_rating", 0.0)), 2),
        rating_count=int(movie.get("rating_count", 0)),
        poster_url=poster.get("poster_url"),
        backdrop_url=poster.get("backdrop_url"),
        overview=poster.get("overview"),
    )


@router.get("/{movie_id}/similar", response_model=List[MovieSummary])
def get_similar_movies(movie_id: int, n: int = Query(10, ge=1, le=30)):
    """Discover top-N similar movies using cosine similarity in 30D SVD latent space."""
    target = recommender_service.get_movie(movie_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found in catalog.",
        )

    similars = recommender_service.get_similar_movies(movie_id, n=n)
    res = []
    for m in similars:
        mid = m["movie_id"]
        poster = poster_service.get_movie_poster(mid, m["title"], m.get("year"))
        res.append(
            MovieSummary(
                movie_id=mid,
                title=m["title"],
                year=m.get("year"),
                genres=m.get("genres", []),
                avg_rating=round(float(m.get("avg_rating", 0.0)), 2),
                rating_count=int(m.get("rating_count", 0)),
                poster_url=poster.get("poster_url"),
            )
        )
    return res
