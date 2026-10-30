"""
Streamlit workflow integration tests using streamlit.testing.v1.AppTest (Phase 4):
- Initial app load without exceptions.
- Empty profile onboarding guidance.
- Movie rating and personalized SVD recommendation generation.
- Cold-start warning badge triggering (< 3 ratings).
- Dynamic N recommendations control adjustment.
- Genre filtering interaction.
- Historical user inspection mode.
- Movie similarity explorer mode.
"""

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def app():
    """Create an AppTest instance for app/streamlit_app.py with a safe timeout."""
    at = AppTest.from_file("app/streamlit_app.py", default_timeout=20)
    at.run()
    return at


def test_app_initial_load(app):
    """Verify the Streamlit app loads cleanly with proper title and controls."""
    assert not app.exception
    assert len(app.title) > 0
    assert "Movie Recommendation System" in app.title[0].value
    # Controls in sidebar
    assert app.slider(key="num_recs_slider").value == 10
    assert app.radio(key="app_mode_radio").value == "Interactive User Profile"


def test_app_empty_profile_guidance(app):
    """Verify that an empty profile renders guidance without crashes."""
    assert not app.exception
    # Check that info message about empty profile is present
    info_messages = [info.value for info in app.info]
    assert any("Profile is empty" in msg for msg in info_messages)


def test_app_cold_start_fallback_label(app):
    """Verify that a profile with 1 rating triggers the cold-start fallback warning banner."""
    app.session_state["user_profile"] = {1: 5.0}  # 1 rating < 3
    app.run()

    assert not app.exception
    warning_messages = [w.value for w in app.warning]
    assert any("Cold-Start Fallback Active" in msg for msg in warning_messages)


def test_app_rate_movie_and_personalized_recommendation(app):
    """Verify that adding >= 3 ratings triggers personalized SVD recommendations."""
    app.session_state["user_profile"] = {1: 5.0, 50: 5.0, 100: 4.0}  # 3 ratings
    app.run()

    assert not app.exception
    success_messages = [s.value for s in app.success]
    assert any("Personalized SVD Active" in msg for msg in success_messages)

    # Verify recommendations table HTML is rendered in markdown
    table_rendered = False
    for md in app.markdown:
        if "dataframe-table" in md.value and "Rank" in md.value:
            table_rendered = True
            break
    assert table_rendered, "Recommendations table should be rendered!"


def test_app_change_n_slider(app):
    """Verify that changing the N slider updates state and reruns without errors."""
    app.session_state["user_profile"] = {1: 5.0, 50: 5.0, 100: 4.0}
    app.run()

    # Change slider to 5
    app.slider(key="num_recs_slider").set_value(5).run()
    assert not app.exception
    assert app.slider(key="num_recs_slider").value == 5


def test_app_genre_filter(app):
    """Verify that selecting a genre filter updates recommendations without errors."""
    app.session_state["user_profile"] = {1: 5.0, 50: 5.0, 100: 4.0}
    app.run()

    # Select Animation genre
    app.multiselect(key="genre_filter").select("Animation").run()
    assert not app.exception
    assert "Animation" in app.multiselect(key="genre_filter").value


def test_app_inspect_historical_user_mode(app):
    """Verify the 'Inspect Historical User' workflow mode."""
    app.radio(key="app_mode_radio").set_value("Inspect Historical User").run()
    assert not app.exception

    # User number input should exist
    assert app.number_input(key="user_id_input").value == 1
    success_messages = [s.value for s in app.success]
    assert any("User 1" in msg for msg in success_messages)


def test_app_movie_similarity_explorer_mode(app):
    """Verify the 'Movie Similarity Explorer' workflow mode."""
    app.radio(key="app_mode_radio").set_value("Movie Similarity Explorer").run()
    assert not app.exception

    # Initial state prompts for search
    info_messages = [info.value for info in app.info]
    assert any("Enter a movie title" in msg for msg in info_messages)

    # Search for Toy Story
    app.text_input(key="similarity_search_input").input("Toy Story").run()
    assert not app.exception
    assert app.selectbox(key="similarity_target_select") is not None
