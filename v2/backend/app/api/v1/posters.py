"""
Poster and artwork delivery endpoints for MovieRec Version 2.
Serves SVG holographic posters and TMDB artwork links.
"""

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse

from app.services.poster_service import poster_service
from app.services.recommender_service import recommender_service

router = APIRouter(prefix="/posters", tags=["Posters & Media"])


@router.get("/{movie_id}")
def get_movie_poster(
    movie_id: int,
    placeholder: bool = Query(False, description="Force holographic SVG placeholder"),
    backdrop: bool = Query(False, description="Prefer horizontal backdrop artwork if available"),
):
    """
    Deliver movie poster artwork for a given movie ID.
    If TMDB artwork is available and placeholder is False, redirects (307) to the remote image URL.
    Otherwise, serves a stylized holographic SVG poster directly with image/svg+xml.
    """
    movie = recommender_service.get_movie(movie_id)
    title = movie["title"] if movie else f"Movie {movie_id}"
    year = movie.get("year") if movie else None

    if not placeholder:
        poster_info = poster_service.get_movie_poster(movie_id, title, year)
        poster_url = (poster_info.get("backdrop_url") if backdrop else poster_info.get("poster_url")) or poster_info.get("poster_url")
        if poster_url and (poster_url.startswith("http://") or poster_url.startswith("https://")):
            return RedirectResponse(url=poster_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    svg_content = poster_service.generate_svg_poster(movie_id, title, year)
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/fallback/{movie_id}")
def get_fallback_poster_svg(movie_id: int):
    """Serve a stylized holographic SVG poster placeholder for a movie."""
    return get_movie_poster(movie_id, placeholder=True)
