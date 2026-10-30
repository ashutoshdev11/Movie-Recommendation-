"""
Application configuration for MovieRec Version 2 Backend.
Uses Pydantic Settings with environment variable overrides.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "MovieRec Version 2 API"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("MOVIEREC_SECRET_KEY", "movierec-v2-super-secret-jwt-key-2026-secure-random-token")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    COOKIE_NAME: str = "movierec_access_token"
    COOKIE_HTTPONLY: bool = True
    COOKIE_SECURE: bool = False  # Set to True for HTTPS in production
    COOKIE_SAMESITE: str = "lax"

    # Database: SQLite default, PostgreSQL compatible
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./v2_database.db")

    # TMDB Poster API
    TMDB_API_KEY: Optional[str] = os.getenv("TMDB_API_KEY", None)
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w500"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env.v2",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
