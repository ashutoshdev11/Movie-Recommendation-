"""
SQLAlchemy 2.0 ORM models for MovieRec Version 2.
Models: User, UserRating, WatchlistItem.
Account IDs are completely distinct and isolated from MovieLens user IDs.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    """Registered application user account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # User-specific interaction relationships
    ratings = relationship("UserRating", back_populates="user", cascade="all, delete-orphan")
    watchlist = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")


class UserRating(Base):
    """User rating interaction with a MovieLens 1M movie."""
    __tablename__ = "user_ratings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, nullable=False, index=True)
    rating = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
    )


class WatchlistItem(Base):
    """User saved movie in personal watchlist."""
    __tablename__ = "user_watchlists"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, nullable=False, index=True)
    added_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="watchlist")

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_watchlist"),
    )
