"""
Pydantic schemas for MovieRec Version 2 authentication, users, movies, ratings, and recommendations.
Enforces strict input validation and zero password exposure.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------------------
# Auth Schemas
# ------------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ------------------------------------------------------------------------------
# Movie & Catalog Schemas
# ------------------------------------------------------------------------------

class MovieSummary(BaseModel):
    movie_id: int
    title: str
    year: Optional[int] = None
    genres: List[str] = []
    avg_rating: float = 0.0
    rating_count: int = 0
    poster_url: Optional[str] = None


class MovieDetails(MovieSummary):
    overview: Optional[str] = None
    backdrop_url: Optional[str] = None


class PaginatedMovies(BaseModel):
    total: int
    page: int
    limit: int
    items: List[MovieSummary]


# ------------------------------------------------------------------------------
# User Ratings Schemas
# ------------------------------------------------------------------------------

class RatingCreate(BaseModel):
    movie_id: int
    rating: float = Field(..., ge=1.0, le=5.0)


class RatingResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    rating: float
    created_at: datetime
    updated_at: datetime
    movie_title: Optional[str] = None
    movie_year: Optional[int] = None
    movie_genres: List[str] = []

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Watchlist Schemas
# ------------------------------------------------------------------------------

class WatchlistAdd(BaseModel):
    movie_id: int


class WatchlistResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    added_at: datetime
    movie_title: Optional[str] = None
    movie_year: Optional[int] = None
    movie_genres: List[str] = []
    poster_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Recommendation Schemas
# ------------------------------------------------------------------------------

class RecommendationItem(BaseModel):
    rank: int
    movie_id: int
    title: str
    year: Optional[int] = None
    genres: List[str] = []
    predicted_rating: float
    avg_rating: float = 0.0
    rating_count: int = 0
    strategy: str
    is_cold_start: bool
    explanation: str
    poster_url: Optional[str] = None


class RecommendationResponse(BaseModel):
    user_id: Optional[int] = None
    strategy: str
    is_cold_start: bool
    count: int
    items: List[RecommendationItem]
