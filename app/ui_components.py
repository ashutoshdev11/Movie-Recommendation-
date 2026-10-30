"""
Modular UI Components for the Holographic 3D Movie Recommendation System.
Generates XSS-safe, modern HTML/CSS components for Streamlit.
"""

import html
import os
from typing import Dict, List, Optional
import streamlit as st


def load_custom_css(css_path: Optional[str] = None) -> None:
    """Inject custom holographic CSS stylesheet into the Streamlit app."""
    if css_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(base_dir, "styles", "holographic.css")
    
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def render_sidebar_branding() -> None:
    """Render the futuristic MovieRec sidebar branding header."""
    st.sidebar.markdown(
        """
        <div class="sidebar-branding">
          <div class="sidebar-logo-icon">🎬</div>
          <div class="sidebar-logo-text">
            <span class="sidebar-logo-title">MovieRec</span>
            <span class="sidebar-logo-tagline">Discover • Explore • Enjoy</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero_section(featured_movie: Dict) -> None:
    """
    Render the futuristic hero banner with gradient title, description,
    genre quick-filter chips, and floating 3D glass featured movie card.
    """
    title = html.escape(str(featured_movie.get("title", "Star Wars (1977)")))
    year = html.escape(str(featured_movie.get("year", "1977") or "1977"))
    genres = featured_movie.get("genres", ["Action", "Adventure", "Sci-Fi"])
    genre_str = html.escape(" • ".join(genres[:3]))
    avg_rating = featured_movie.get("avg_rating", 4.36)
    rating_count = featured_movie.get("rating_count", 583)
    
    # Genuine synopsis / description based on actual movie metadata
    desc = html.escape(
        featured_movie.get(
            "desc",
            f"Academic benchmark champion in MovieLens 100K. "
            f"Rated by {rating_count} historical users with a training average of {avg_rating:.2f} stars."
        )
    )

    hero_html = f"""
    <div class="hero-wrapper">
      <div style="display: flex; gap: 30px; align-items: center; flex-wrap: wrap;">
        <!-- Left Hero Column -->
        <div style="flex: 1.2; min-width: 320px;">
          <div class="hero-pill-badge">✨ AI POWERED RECOMMENDATIONS</div>
          <div class="hero-heading">
            Discover Your Next <br><span class="gradient-text">Favourite Movie</span>
          </div>
          <div class="hero-subtitle">
            Personalized recommendations, powered by Collaborative Filtering.
            Find movies you'll love based on your taste, historical patterns, and latent factor similarity.
          </div>
          
          <div class="genre-chips-container">
            <span class="genre-chip">Action</span>
            <span class="genre-chip">Adventure</span>
            <span class="genre-chip">Sci-Fi</span>
            <span class="genre-chip">Drama</span>
            <span class="genre-chip">Comedy</span>
            <span class="genre-chip">Thriller</span>
            <span class="genre-chip">Romance</span>
            <span class="genre-chip">Horror</span>
          </div>
        </div>

        <!-- Right Hero Column: 3D Holographic Featured Movie Card -->
        <div style="flex: 0.9; min-width: 290px;">
          <div class="featured-card-3d">
            <div class="featured-badge">FEATURED</div>
            <div class="featured-title">{title}</div>
            <div class="featured-meta">
              <span>{year}</span>
              <span>•</span>
              <span>{genre_str}</span>
              <span>•</span>
              <span class="featured-rating">★ {avg_rating:.1f}/5.0</span>
            </div>
            <div class="featured-desc">{desc}</div>
            <div style="display: flex; gap: 10px; align-items: center;">
              <div style="padding: 6px 14px; border-radius: 9999px; background: rgba(0, 240, 255, 0.15); border: 1px solid #00f0ff; color: #00f0ff; font-size: 0.8rem; font-weight: 600;">
                🔥 Most Rated Catalog Movie
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)


def get_movie_genre_icon(genres: List[str]) -> str:
    """Return an appropriate emoji icon based on primary movie genre."""
    if not genres:
        return "🎬"
    g = genres[0].lower()
    if "action" in g or "adventure" in g:
        return "⚔️"
    if "sci-fi" in g:
        return "🚀"
    if "comedy" in g:
        return "🎭"
    if "drama" in g:
        return "🎞️"
    if "thriller" in g or "crime" in g or "mystery" in g:
        return "🔍"
    if "romance" in g:
        return "💖"
    if "horror" in g:
        return "👁️"
    if "animation" in g or "children" in g:
        return "🎨"
    if "documentary" in g:
        return "📹"
    if "western" in g:
        return "🤠"
    return "🎬"


def render_movie_card_html(movie: Dict, badge_label: Optional[str] = None) -> str:
    """Generate safe HTML for a single 3D holographic movie card."""
    title = html.escape(str(movie.get("title", "Untitled")))
    year = html.escape(str(movie.get("year", "") or ""))
    genres = movie.get("genres", [])
    primary_genre = html.escape(genres[0] if genres else "General")
    icon = get_movie_genre_icon(genres)
    
    score = movie.get("predicted_rating", movie.get("avg_rating", 0.0))
    rating_display = f"{float(score):.1f}★"
    
    badge_html = f'<div class="movie-poster-badge">{html.escape(badge_label)}</div>' if badge_label else f'<div class="movie-poster-badge">{primary_genre}</div>'

    return f"""
    <div class="movie-poster-card">
      <div class="movie-poster-art">
        {badge_html}
        <div class="movie-poster-center-icon">{icon}</div>
        <div style="font-size: 0.65rem; color: #94a3b8; text-transform: uppercase;">{html.escape(primary_genre)}</div>
      </div>
      <div class="movie-card-title" title="{title}">{title}</div>
      <div class="movie-card-footer">
        <span class="movie-card-rating">{rating_display}</span>
        <span class="movie-card-year">{year}</span>
      </div>
    </div>
    """


def render_trending_carousel(trending_movies: List[Dict]) -> None:
    """Render the horizontal trending movies carousel container."""
    cards_html = "".join([render_movie_card_html(m, badge_label="TRENDING") for m in trending_movies[:6]])
    section_html = f"""
    <div style="margin-top: 24px; margin-bottom: 24px;">
      <div class="trending-header">
        <div class="trending-title">🔥 Trending Now</div>
      </div>
      <div class="trending-grid">
        {cards_html}
      </div>
    </div>
    """
    st.markdown(section_html, unsafe_allow_html=True)


def render_three_feature_cards() -> None:
    """
    Render the 3 main holographic recommendation feature cards:
    1. Profile Builder
    2. Historical User Inspector
    3. Similarity Explorer
    Matching the layout, badges, and structure of the reference image.
    """
    cards_html = """
    <div class="features-container">
      <!-- Card 1: Profile Builder -->
      <div class="feature-hub-card">
        <div class="feature-hub-header">
          <div class="feature-badge-number">1</div>
          <div class="feature-header-text">
            <div class="feature-hub-title">Profile Builder</div>
            <div class="feature-hub-desc">Rate favourite movies and get personalized SVD recommendations based on your taste.</div>
          </div>
          <div class="feature-hub-icon-bubble">✨</div>
        </div>
        
        <div class="feature-inner-preview">
          <div style="font-size: 0.75rem; font-weight: 600; color: #00f0ff; margin-bottom: 8px;">TASTE PROFILE PREVIEW</div>
          <div class="mini-genre-bar">
            <div class="mini-genre-label"><span>Sci-Fi</span><span>35%</span></div>
            <div class="mini-progress-track"><div class="mini-progress-fill" style="width: 35%;"></div></div>
          </div>
          <div class="mini-genre-bar">
            <div class="mini-genre-label"><span>Action</span><span>25%</span></div>
            <div class="mini-progress-track"><div class="mini-progress-fill" style="width: 25%;"></div></div>
          </div>
          <div class="mini-genre-bar">
            <div class="mini-genre-label"><span>Drama</span><span>20%</span></div>
            <div class="mini-progress-track"><div class="mini-progress-fill" style="width: 20%;"></div></div>
          </div>
        </div>
        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: auto; padding-top: 6px;">
          Active Mode: Latent folding-in for ≥3 ratings, damped popularity for &lt;3.
        </div>
      </div>

      <!-- Card 2: Historical User Inspector -->
      <div class="feature-hub-card">
        <div class="feature-hub-header">
          <div class="feature-badge-number">2</div>
          <div class="feature-header-text">
            <div class="feature-hub-title">Historical User Inspector</div>
            <div class="feature-hub-desc">Explore a user's past ratings, preferences, and recommendations from MovieLens 100K.</div>
          </div>
          <div class="feature-hub-icon-bubble">👤</div>
        </div>
        
        <div class="feature-inner-preview">
          <div style="font-size: 0.75rem; font-weight: 600; color: #a855f7; margin-bottom: 8px;">USER REPOSITORY</div>
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px; color: #cbd5e1;">
            <span>Users in Benchmark:</span><strong>943 Users</strong>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px; color: #cbd5e1;">
            <span>Total Ratings:</span><strong>100,000 Ratings</strong>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #cbd5e1;">
            <span>Champion Model:</span><strong>Truncated SVD (k=20)</strong>
          </div>
        </div>
        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: auto; padding-top: 6px;">
          Examine individual user histories and personalized rank orders.
        </div>
      </div>

      <!-- Card 3: Similarity Explorer -->
      <div class="feature-hub-card">
        <div class="feature-hub-header">
          <div class="feature-badge-number">3</div>
          <div class="feature-header-text">
            <div class="feature-hub-title">Similarity Explorer</div>
            <div class="feature-hub-desc">Enter any movie to discover other catalog titles with highest latent factor cosine similarity.</div>
          </div>
          <div class="feature-hub-icon-bubble">🔍</div>
        </div>
        
        <div class="feature-inner-preview">
          <div style="font-size: 0.75rem; font-weight: 600; color: #ec4899; margin-bottom: 8px;">LATENT FACTOR SIMILARITY</div>
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px; color: #cbd5e1;">
            <span>Metric:</span><strong>20D Cosine Angle</strong>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px; color: #cbd5e1;">
            <span>Item Coverage:</span><strong>1,682 Movies</strong>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #cbd5e1;">
            <span>Speed:</span><strong>&lt; 1 ms per query</strong>
          </div>
        </div>
        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: auto; padding-top: 6px;">
          Compute pairwise cosine distances in fitted right singular vector space.
        </div>
      </div>
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)


def render_stats_overview(total_users: int = 943, total_movies: int = 1682, total_ratings: int = 100000, avg_rating: float = 3.53) -> None:
    """Render real project dataset statistics in futuristic glowing metric boxes."""
    html_content = f"""
    <div class="stats-banner">
      <div class="stat-box">
        <div class="stat-value">{total_ratings:,}</div>
        <div class="stat-label">Ratings Analyzed</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">{total_users:,}</div>
        <div class="stat-label">Active Users</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">{total_movies:,}</div>
        <div class="stat-label">Catalog Movies</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">{avg_rating:.2f}★</div>
        <div class="stat-label">Dataset Rating Mean</div>
      </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)


def render_footer() -> None:
    """Render the cinematic platform footer."""
    st.markdown(
        """
        <div class="app-footer">
          <div class="footer-brand">
            <span>🎬 MovieRec</span>
            <span style="font-size: 0.75rem; color: #64748b;">| Better Movies, Better You</span>
          </div>
          <div>Movie Recommendation System • Powered by Machine Learning 🧠</div>
          <div style="color: #00f0ff;">❤️ Built with Streamlit</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
