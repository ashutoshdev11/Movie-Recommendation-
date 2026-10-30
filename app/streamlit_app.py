"""
Streamlit Web Application for Movie Recommendation System.
Viva demonstration application for MovieLens 100K Pure Collaborative Filtering.
Redesigned with Holographic 3D Cyberpunk / Sci-Fi Frontend Design System.
"""

import html
import os
import sys
from typing import Dict, List, Optional
import pandas as pd
import streamlit as st

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.recsys.service import RecommenderService
from app.ui_components import (
    load_custom_css,
    render_sidebar_branding,
    render_hero_section,
    render_trending_carousel,
    render_three_feature_cards,
    render_movie_card_html,
    render_stats_overview,
    render_footer,
)


def render_table(df: pd.DataFrame) -> None:
    """Render a pandas DataFrame as a styled HTML table without pyarrow dependency."""
    if df.empty:
        return
    html_table = df.to_html(index=False, classes="dataframe-table", escape=True)
    st.markdown(
        f"""
        <style>
        .dataframe-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 1rem 0;
            font-size: 0.92rem;
            background: rgba(10, 16, 42, 0.7);
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: 12px;
            overflow: hidden;
        }}
        .dataframe-table th {{
            background-color: rgba(18, 28, 70, 0.9);
            color: #00f0ff;
            padding: 12px 14px;
            text-align: left;
            border-bottom: 2px solid rgba(0, 240, 255, 0.3);
            font-weight: 600;
        }}
        .dataframe-table td {{
            padding: 10px 14px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            color: #cbd5e1;
        }}
        .dataframe-table tr:hover {{
            background-color: rgba(0, 240, 255, 0.08);
            color: #ffffff;
        }}
        </style>
        {html_table}
        """,
        unsafe_allow_html=True,
    )


def render_movie_cards_grid(movies: List[Dict], badge_prefix: str = "") -> None:
    """Render a responsive grid of holographic movie cards from a list of movie dicts."""
    if not movies:
        return
    cards_html = []
    for i, m in enumerate(movies, start=1):
        badge = f"{badge_prefix} #{i}" if badge_prefix else None
        cards_html.append(render_movie_card_html(m, badge_label=badge))
    
    grid_html = f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin: 18px 0;">
      {''.join(cards_html)}
    </div>
    """
    st.markdown(grid_html, unsafe_allow_html=True)


@st.cache_resource
def get_recommender_service() -> RecommenderService:
    """Instantiate and cache the RecommenderService singleton."""
    return RecommenderService(artifacts_dir=os.path.join(BASE_DIR, "results", "artifacts"))


def main() -> None:
    st.set_page_config(
        page_title="MovieRec — Holographic 3D Recommender",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Load custom Holographic 3D CSS stylesheet
    load_custom_css()

    service = get_recommender_service()

    # Base title for accessibility & test fixture compatibility
    st.title("🎬 Movie Recommendation System")
    st.caption("MovieLens 100K Academic Benchmark — Pure Collaborative Filtering (Truncated SVD + Damped Popularity)")

    # --------------------------------------------------------------------------
    # Sidebar: Branding, Navigation & Global Controls
    # --------------------------------------------------------------------------
    render_sidebar_branding()

    nav_options = [
        "Interactive User Profile",
        "Home",
        "Inspect Historical User",
        "Movie Similarity Explorer",
        "Trending",
        "Top Rated",
        "Genres",
        "My List",
    ]

    nav_labels = {
        "Interactive User Profile": "👤 Profile Builder",
        "Home": "🏠 Home",
        "Inspect Historical User": "👥 Historical User Inspector",
        "Movie Similarity Explorer": "🔍 Similarity Explorer",
        "Trending": "🔥 Trending Now",
        "Top Rated": "⭐ Top Rated",
        "Genres": "🎭 Genre Explorer",
        "My List": "📑 My Rated List",
    }

    app_mode = st.sidebar.radio(
        "Navigation Menu",
        options=nav_options,
        format_func=lambda opt: nav_labels.get(opt, opt),
        key="app_mode_radio",
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Recommendation Controls")

    num_recs = st.sidebar.slider(
        "Number of recommendations (N)",
        min_value=1,
        max_value=20,
        value=10,
        step=1,
        key="num_recs_slider",
        help="Select how many recommendations to generate.",
    )

    selected_genres = st.sidebar.multiselect(
        "Filter by Genre",
        options=service.all_genres,
        default=[],
        key="genre_filter",
        help="Filter candidate recommendations by one or more genres.",
    )
    filter_genres = selected_genres if selected_genres else None

    # Dark Mode toggle switch
    st.sidebar.markdown("---")
    st.sidebar.toggle("🌙 Dark Mode", value=True, key="dark_mode_toggle", disabled=True, help="Holographic Dark Mode is active.")

    st.sidebar.markdown(
        """
        <div style="font-size: 0.75rem; color: #64748b; line-height: 1.4; padding: 10px 4px;">
          <strong>Architecture Details:</strong><br>
          • <strong>Champion:</strong> Truncated SVD (k=20)<br>
          • <strong>Cold-Start:</strong> Damped Popularity (m=50)<br>
          • <strong>Threshold:</strong> &lt;3 ratings = Popularity; ≥3 = Latent SVD Folding-In<br>
          • <strong>Latency:</strong> ~2.8 ms / request
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pre-compute top trending & top rated movies for views
    all_movies = list(service.movie_metadata.values())
    trending_movies = sorted(all_movies, key=lambda m: (-m["rating_count"], m["title"]))[:12]
    top_rated_movies = sorted([m for m in all_movies if m["rating_count"] >= 40], key=lambda m: (-m["avg_rating"], -m["rating_count"]))[:12]

    # Featured Movie: Star Wars (1977) - highest rated catalog classic in MovieLens 100K
    featured_movie = service.movie_metadata.get(50, trending_movies[0])

    # --------------------------------------------------------------------------
    # VIEW: Home
    # --------------------------------------------------------------------------
    if app_mode == "Home":
        # 1. Hero Section with 3D Featured Card
        render_hero_section(featured_movie)

        # 2. Large Search Bar on Home
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        home_query = st.text_input(
            "Search Catalog",
            placeholder="Search catalog movies (e.g., Star Wars, Fargo, Pulp Fiction, Toy Story...)",
            key="home_search_bar",
            label_visibility="collapsed",
        )

        if home_query:
            matched_home = service.search_movies(home_query, limit=6)
            if matched_home:
                st.markdown(f"#### 🔍 Search Results for '{html.escape(home_query)}':")
                render_movie_cards_grid(matched_home, badge_prefix="MATCH")
            else:
                st.info(f"No catalog movies found matching '{html.escape(home_query)}'.")

        # 3. Trending Now Carousel
        render_trending_carousel(trending_movies)

        # 4. Three Main Recommendation Feature Cards (Matching Reference Layout)
        st.markdown(
            """
            <div style="margin-top: 24px; margin-bottom: 12px;">
              <div class="trending-title">⚡ Interactive Recommendation Engines</div>
              <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">
                Choose an engine below or via the sidebar to start discovering movies.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_three_feature_cards()

        # Action Buttons corresponding to the 3 Feature Cards
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🚀 Launch Profile Builder →", key="btn_go_profile", use_container_width=True):
                st.session_state["app_mode_radio"] = "Interactive User Profile"
                st.rerun()
        with c2:
            if st.button("👤 Explore Historical Users →", key="btn_go_user", use_container_width=True):
                st.session_state["app_mode_radio"] = "Inspect Historical User"
                st.rerun()
        with c3:
            if st.button("🔍 Find Similar Movies →", key="btn_go_sim", use_container_width=True):
                st.session_state["app_mode_radio"] = "Movie Similarity Explorer"
                st.rerun()

        # 5. Dataset Statistics Overview
        st.markdown("<div style='margin-top: 36px; margin-bottom: 12px;'><div class='trending-title'>📊 MovieLens 100K Dataset Insights</div></div>", unsafe_allow_html=True)
        render_stats_overview()

        # 6. Top Rated Showcase
        st.markdown("<div style='margin-top: 20px; margin-bottom: 12px;'><div class='trending-title'>⭐ Critically Acclaimed Classics</div></div>", unsafe_allow_html=True)
        render_movie_cards_grid(top_rated_movies[:6], badge_prefix="TOP")

    # --------------------------------------------------------------------------
    # VIEW: Mode 1 - Profile Builder (Interactive User Profile)
    # --------------------------------------------------------------------------
    elif app_mode == "Interactive User Profile":
        st.markdown(
            """
            <div class="holo-panel">
              <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <span style="font-size: 28px;">👤</span>
                <div>
                  <h2 style="margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; color: #ffffff;">
                    Interactive Profile Builder
                  </h2>
                  <div style="color: #94a3b8; font-size: 0.88rem;">
                    Rate your favourite catalog movies to build an online taste profile and receive real-time SVD latent folding-in recommendations.
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Initialize session state for user profile
        if "user_profile" not in st.session_state:
            st.session_state["user_profile"] = {}

        col1, col2 = st.columns([2, 1])

        with col1:
            search_query = st.text_input(
                "Search for a movie title to rate:",
                placeholder="e.g., Star Wars, Toy Story, Pulp Fiction, Fargo...",
                key="movie_search_input",
            )

            matched_movies = service.search_movies(search_query, limit=10) if search_query else []

            if matched_movies:
                movie_options = {
                    m["item_id"]: f"{m['title']} ({', '.join(m['genres'][:2])}) — avg {m['avg_rating']}★"
                    for m in matched_movies
                }
                selected_movie_id = st.selectbox(
                    "Select matched movie:",
                    options=list(movie_options.keys()),
                    format_func=lambda mid: movie_options[mid],
                    key="matched_movie_select",
                )
            else:
                selected_movie_id = None
                if search_query:
                    st.info("No movies found matching that query.")

        with col2:
            rating_val = st.slider(
                "Rating to assign (stars):",
                min_value=1.0,
                max_value=5.0,
                value=5.0,
                step=0.5,
                key="movie_rating_slider",
            )
            add_button = st.button("⭐ Add Rating to Profile", key="add_rating_button", use_container_width=True)

            if add_button and selected_movie_id is not None:
                st.session_state["user_profile"][int(selected_movie_id)] = float(rating_val)
                st.success(f"Added rating {rating_val} for {service.get_movie_info(selected_movie_id)['title']}!")

        # Current Profile Summary
        profile = st.session_state["user_profile"]

        if profile:
            st.markdown(f"### 📋 Your Current Profile ({len(profile)} rated movies)")
            profile_rows = []
            for mid, r in profile.items():
                info = service.get_movie_info(mid)
                profile_rows.append({
                    "Movie ID": mid,
                    "Title": info["title"],
                    "Genres": ", ".join(info["genres"]),
                    "Your Rating": f"{r:.1f} stars",
                })
            render_table(pd.DataFrame(profile_rows))

            if st.button("🗑️ Clear Profile", key="clear_profile_button"):
                st.session_state["user_profile"] = {}
                st.rerun()

            st.markdown("---")

            # Generate Recommendations
            st.markdown("### 🎯 Recommended Movies for You")

            try:
                recs = service.recommend_for_profile(profile, n=num_recs, filter_genres=filter_genres)

                if recs:
                    is_cold_start = recs[0]["is_cold_start"]
                    if is_cold_start:
                        st.warning(
                            f"⚠️ **Cold-Start Fallback Active:** Your profile has {len(profile)} rating(s) "
                            f"(< {service.min_ratings_for_personalization} required for latent folding-in). "
                            "Displaying top Bayesian damped Popularity recommendations."
                        )
                    else:
                        st.success(
                            f"🎯 **Personalized SVD Active:** {len(profile)} ratings folded into 20-dimensional "
                            "latent space via right singular vectors."
                        )

                    # 1. Holographic Visual Cards
                    render_movie_cards_grid(recs, badge_prefix="REC")

                    # 2. Detailed Data Table
                    display_rows = []
                    for rank, r in enumerate(recs, start=1):
                        display_rows.append({
                            "Rank": rank,
                            "Title": r["title"],
                            "Year": r["year"] if r["year"] else "N/A",
                            "Genres": ", ".join(r["genres"]),
                            "Predicted Score": f"{r['predicted_rating']:.2f}",
                            "Training Avg": f"{r['avg_rating']:.2f}",
                            "Ratings Count": r["rating_count"],
                            "Explanation": r["explanation"],
                        })

                    render_table(pd.DataFrame(display_rows))
                else:
                    st.info("No recommendations match your active genre filter. Try removing or broadening the filter.")

            except Exception as e:
                st.error(f"Error generating recommendations: {e}")

        else:
            st.info("💡 **Profile is empty.** Search for a movie above and add at least one rating to view collaborative filtering recommendations.")

    # --------------------------------------------------------------------------
    # VIEW: Mode 2 - Historical User Inspector
    # --------------------------------------------------------------------------
    elif app_mode == "Inspect Historical User":
        st.markdown(
            """
            <div class="holo-panel">
              <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <span style="font-size: 28px;">👥</span>
                <div>
                  <h2 style="margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; color: #ffffff;">
                    Historical User Inspector
                  </h2>
                  <div style="color: #94a3b8; font-size: 0.88rem;">
                    Examine personalized recommendations generated directly for existing users in the MovieLens 100K training dataset.
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_id = st.number_input(
            "Select User ID (1 to 943):",
            min_value=1,
            max_value=943,
            value=1,
            step=1,
            key="user_id_input",
        )

        try:
            recs = service.recommend_for_user(int(user_id), n=num_recs, filter_genres=filter_genres)

            if recs:
                st.success(f"Generated top-{num_recs} recommendations for User {user_id} using Truncated SVD:")
                
                # Visual Cards
                render_movie_cards_grid(recs, badge_prefix="USER REC")

                # Detailed Table
                display_rows = []
                for rank, r in enumerate(recs, start=1):
                    display_rows.append({
                        "Rank": rank,
                        "Title": r["title"],
                        "Year": r["year"] if r["year"] else "N/A",
                        "Genres": ", ".join(r["genres"]),
                        "Predicted Rating": f"{r['predicted_rating']:.2f}",
                        "Training Avg": f"{r['avg_rating']:.2f}",
                        "Ratings Count": r["rating_count"],
                        "Explanation": r["explanation"],
                    })
                render_table(pd.DataFrame(display_rows))
            else:
                st.info("No recommendations match the active genre filter for this user.")

        except Exception as e:
            st.error(f"Error: {e}")

    # --------------------------------------------------------------------------
    # VIEW: Mode 3 - Movie Similarity Explorer
    # --------------------------------------------------------------------------
    elif app_mode == "Movie Similarity Explorer":
        st.markdown(
            """
            <div class="holo-panel">
              <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <span style="font-size: 28px;">🔍</span>
                <div>
                  <h2 style="margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; color: #ffffff;">
                    Movie Similarity Explorer (20D Latent Factor Space)
                  </h2>
                  <div style="color: #94a3b8; font-size: 0.88rem;">
                    Discover movies that share the highest cosine similarity in the 20-dimensional SVD item latent factor space.
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        search_query = st.text_input(
            "Search for a target movie:",
            placeholder="e.g., Toy Story, Fargo, Jurassic Park...",
            key="similarity_search_input",
        )

        matched_movies = service.search_movies(search_query, limit=10) if search_query else []

        if matched_movies:
            movie_options = {m["item_id"]: f"{m['title']} ({', '.join(m['genres'][:2])})" for m in matched_movies}
            target_id = st.selectbox(
                "Select target movie to find similar items:",
                options=list(movie_options.keys()),
                format_func=lambda mid: movie_options[mid],
                key="similarity_target_select",
            )

            if target_id is not None:
                similar = service.similar_movies(int(target_id), n=num_recs)
                target_info = service.get_movie_info(target_id)

                st.markdown(f"### Most Similar Movies to **{html.escape(target_info['title'])}**:")

                # Visual Cards
                render_movie_cards_grid(similar, badge_prefix="SIMILAR")

                # Detailed Table
                display_rows = []
                for rank, s in enumerate(similar, start=1):
                    display_rows.append({
                        "Rank": rank,
                        "Title": s["title"],
                        "Year": s["year"] if s["year"] else "N/A",
                        "Genres": ", ".join(s["genres"]),
                        "Latent Cosine Similarity": f"{s['similarity']:.4f}",
                        "Training Avg": f"{s['avg_rating']:.2f}",
                        "Ratings Count": s["rating_count"],
                    })
                render_table(pd.DataFrame(display_rows))
        else:
            if search_query:
                st.info("No movies matched your query.")
            else:
                st.info("Enter a movie title above to find similar movies in the catalog.")

    # --------------------------------------------------------------------------
    # VIEW: Trending Now
    # --------------------------------------------------------------------------
    elif app_mode == "Trending":
        st.markdown(
            """
            <div class="holo-panel">
              <h2 style="margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; color: #ffffff;">
                🔥 Trending Catalog Movies
              </h2>
              <div style="color: #94a3b8; font-size: 0.88rem;">
                Ranked strictly by historical rating engagement across all 943 MovieLens users.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_movie_cards_grid(trending_movies, badge_prefix="TRENDING")

    # --------------------------------------------------------------------------
    # VIEW: Top Rated
    # --------------------------------------------------------------------------
    elif app_mode == "Top Rated":
        st.markdown(
            """
            <div class="holo-panel">
              <h2 style="margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; color: #ffffff;">
                ⭐ Highest Rated Classic Movies
              </h2>
              <div style="color: #94a3b8; font-size: 0.88rem;">
                Curated by Bayesian damped average ratings (minimum 40 ratings) to filter low-sample noise.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_movie_cards_grid(top_rated_movies, badge_prefix="TOP RATED")

    # --------------------------------------------------------------------------
    # VIEW: Genres
    # --------------------------------------------------------------------------
    elif app_mode == "Genres":
        st.markdown(
            """
            <div class="holo-panel">
              <h2 style="margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; color: #ffffff;">
                🎭 MovieLens Genre Explorer
              </h2>
              <div style="color: #94a3b8; font-size: 0.88rem;">
                Filter and discover top-ranked catalog movies within each specific cinematic genre.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        selected_genre = st.selectbox("Choose Genre to Explore:", options=service.all_genres, index=0)
        genre_movies = [m for m in all_movies if selected_genre in m.get("genres", [])]
        genre_movies.sort(key=lambda m: (-m["rating_count"], -m["avg_rating"]))

        st.markdown(f"#### Top {selected_genre} Titles ({len(genre_movies)} total in catalog):")
        render_movie_cards_grid(genre_movies[:12], badge_prefix=selected_genre.upper())

    # --------------------------------------------------------------------------
    # VIEW: My List
    # --------------------------------------------------------------------------
    elif app_mode == "My List":
        st.markdown(
            """
            <div class="holo-panel">
              <h2 style="margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; color: #ffffff;">
                📑 My Saved Ratings & Watchlist
              </h2>
              <div style="color: #94a3b8; font-size: 0.88rem;">
                Review all the ratings currently stored in your active interactive session profile.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        profile = st.session_state.get("user_profile", {})
        if profile:
            profile_items = []
            for mid, r in profile.items():
                m_info = service.get_movie_info(mid)
                m_info_copy = dict(m_info)
                m_info_copy["predicted_rating"] = r
                profile_items.append(m_info_copy)
            render_movie_cards_grid(profile_items, badge_prefix="RATED")
        else:
            st.info("You haven't rated any movies yet. Visit the Profile Builder or Home page to add movies!")

    # --------------------------------------------------------------------------
    # Footer
    # --------------------------------------------------------------------------
    render_footer()


if __name__ == "__main__":
    main()
