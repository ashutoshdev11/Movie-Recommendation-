# Phase 4: Recommendation Service and Streamlit App

Prerequisite: Phase 3 audit = PASS. Use the model selected in Phase 3.

## Tasks
1. `src/recsys/service.py` with a `RecommenderService`: load or cache fitted artifacts (only load files this project produced), `recommend_for_user`, `recommend_for_profile` (a new user's ratings folded in as an extra user row), `similar_movies`, `search_movies`.
2. Transparent cold-start fallback: if a profile has fewer than a documented minimum number of ratings, return popularity results and label them as such.
3. Input validation with clear errors: unknown user, unknown movie, rating outside 1..5, empty profile.
4. `app/streamlit_app.py`: title and introduction, movie search/select, rating entry, number-of-recommendations control, genre filter, results table (title, year, genres, predicted rating only where the model supports it, otherwise average rating and rating count).
5. Explanations only from real model signals (for example, the user's rated movies that contributed most to an item-based score).
6. Graceful handling of empty input and empty results; no non-functional buttons; no fabricated posters or metadata.
7. Tests: service unit and integration tests; Streamlit workflow tests with `streamlit.testing.v1.AppTest`.
8. Document the public service interface.

## Acceptance criteria
- [ ] Service returns the same recommendations as calling the model directly (test).
- [ ] No already-rated movie is ever returned; predictions within [1, 5] (tests).
- [ ] Each error case in task 3 has a test and a readable message.
- [ ] Cold-start fallback is triggered by a test profile and is labelled in the output.
- [ ] `streamlit run app/streamlit_app.py` starts without errors (observed).
- [ ] AppTest covers: rate movies and get recommendations; empty profile; changing N; genre filter.
- [ ] Every UI control changes something real (verified by test or inspection).
- [ ] `pytest` passes with 0 failures (observed output).

## Audit checklist
Start the app, rate 5 movies, and compare what the page shows with a direct service call; try invalid input; read the explanation code to confirm it uses real model values.
