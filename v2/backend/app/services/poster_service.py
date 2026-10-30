"""
Movie Poster and Artwork Service for MovieRec Version 2.
Integrates with The Movie Database (TMDB) API with aggressive disk caching and SVG fallbacks.
"""

import json
import os
import re
from typing import Dict, Optional
import httpx

from app.core.config import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "cache", "posters")
os.makedirs(CACHE_DIR, exist_ok=True)


class PosterService:
    """Provides movie poster artwork with local disk caching and graceful fallback handling."""

    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.image_base_url = settings.TMDB_IMAGE_BASE_URL

    def _get_cache_filepath(self, movie_id: int) -> str:
        return os.path.join(CACHE_DIR, f"poster_{movie_id}.json")

    def get_movie_poster(
        self,
        movie_id: int,
        title: str,
        year: Optional[int] = None,
    ) -> Dict[str, Optional[str]]:
        """
        Fetch poster and backdrop URLs for movie. Checks local disk cache first.
        If no TMDB API key is configured or API fails, returns an SVG fallback URL.
        """
        cache_path = self._get_cache_filepath(movie_id)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # If no API key configured, use graceful fallback
        if not self.api_key:
            fallback = {
                "movie_id": movie_id,
                "poster_url": f"/api/v1/posters/fallback/{movie_id}",
                "backdrop_url": None,
                "overview": None,
                "source": "fallback_placeholder",
            }
            return fallback

        # Query TMDB API
        try:
            params = {
                "api_key": self.api_key,
                "query": title,
                "include_adult": "false",
            }
            if year:
                params["year"] = str(year)

            resp = httpx.get(
                f"{self.base_url}/search/movie",
                params=params,
                timeout=4.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    top_match = results[0]
                    poster_path = top_match.get("poster_path")
                    backdrop_path = top_match.get("backdrop_path")
                    overview = top_match.get("overview")

                    poster_url = f"{self.image_base_url}{poster_path}" if poster_path else None
                    backdrop_url = f"{self.image_base_url}{backdrop_path}" if backdrop_path else None

                    cached_data = {
                        "movie_id": movie_id,
                        "poster_url": poster_url or f"/api/v1/posters/fallback/{movie_id}",
                        "backdrop_url": backdrop_url,
                        "overview": overview,
                        "source": "tmdb",
                    }

                    # Save to cache
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(cached_data, f)
                    return cached_data
        except Exception:
            pass

        # Fallback if network fails or no match found
        fallback = {
            "movie_id": movie_id,
            "poster_url": f"/api/v1/posters/fallback/{movie_id}",
            "backdrop_url": None,
            "overview": None,
            "source": "fallback_placeholder",
        }
        return fallback

    def generate_svg_poster(self, movie_id: int, title: str, year: Optional[int] = None) -> str:
        """Generate a sleek, futuristic SVG movie poster placeholder."""
        year_str = str(year) if year else ""
        escaped_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Split long title across two lines if necessary
        line1 = escaped_title
        line2 = ""
        if len(escaped_title) > 22:
            words = escaped_title.split()
            mid = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450" width="300" height="450">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a102b"/>
      <stop offset="50%" stop-color="#141c46"/>
      <stop offset="100%" stop-color="#070a1c"/>
    </linearGradient>
    <linearGradient id="neon" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f0ff"/>
      <stop offset="100%" stop-color="#a855f7"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="30%" r="50%">
      <stop offset="0%" stop-color="#00f0ff" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#00f0ff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  
  <rect width="300" height="450" fill="url(#bg)" rx="16"/>
  <rect width="296" height="446" x="2" y="2" fill="none" stroke="url(#neon)" stroke-width="2" rx="14" opacity="0.6"/>
  <circle cx="150" cy="140" r="100" fill="url(#glow)"/>
  
  <!-- Film Reel Hologram -->
  <circle cx="150" cy="150" r="42" fill="none" stroke="#00f0ff" stroke-width="3" opacity="0.8"/>
  <circle cx="150" cy="150" r="14" fill="#a855f7" opacity="0.9"/>
  <circle cx="150" cy="122" r="6" fill="#00f0ff"/>
  <circle cx="150" cy="178" r="6" fill="#00f0ff"/>
  <circle cx="122" cy="150" r="6" fill="#00f0ff"/>
  <circle cx="178" cy="150" r="6" fill="#00f0ff"/>
  
  <!-- Typography -->
  <text x="150" y="270" text-anchor="middle" fill="#ffffff" font-family="'Space Grotesk', system-ui, sans-serif" font-weight="700" font-size="20">{line1}</text>
  <text x="150" y="296" text-anchor="middle" fill="#ffffff" font-family="'Space Grotesk', system-ui, sans-serif" font-weight="700" font-size="18">{line2}</text>
  
  <rect x="110" y="325" width="80" height="24" rx="12" fill="rgba(0, 240, 255, 0.15)" stroke="#00f0ff" stroke-width="1"/>
  <text x="150" y="341" text-anchor="middle" fill="#00f0ff" font-family="system-ui, sans-serif" font-weight="600" font-size="12">{year_str}</text>
  
  <text x="150" y="415" text-anchor="middle" fill="#64748b" font-family="system-ui, sans-serif" font-size="11" letter-spacing="1.5">MOVIEREC V2</text>
</svg>"""
        return svg


poster_service = PosterService()
