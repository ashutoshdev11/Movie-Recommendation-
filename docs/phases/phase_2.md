# Phase 2: Collaborative-Filtering Engine

Prerequisite: Phase 1 audit = PASS. Evaluation is Phase 3; do not tune or report final metrics here.

## Common interface (all models in `src/recsys/models/`)
`fit(train_ratings)`, `predict(user_id, item_id) -> float`, `recommend(user_id, n, exclude_seen=True) -> list[(item_id, score)]`. All training-dependent statistics (means, similarities) are computed inside `fit` from the training data only.

## Tasks
1. Build a sparse user-item matrix (CSR) with ID-to-index mappings. Missing means missing.
2. **Popularity baseline**: damped mean rating with a global-mean prior and minimum-vote parameter; rank by it.
3. **User-based kNN**: mean-centred ratings, Pearson (or cosine on mean-centred data), minimum overlap, top-k neighbours who rated the item.
   Prediction: r_hat(u,i) = mean_u + sum_v s(u,v)(r_vi - mean_v) / sum_v |s(u,v)|.
4. **Item-based kNN**: adjusted cosine (subtract user means), top-k similar items the user has rated.
   Prediction: r_hat(u,i) = sum_j s(i,j) r_uj / sum_j |s(i,j)|.
5. **SVD benchmark**: user-mean-centred matrix, truncated SVD with `scipy.sparse.linalg.svds`; number of factors configurable.
6. Fallback chain when neighbours are insufficient or the denominator is zero: item mean, then user mean, then global mean. Clip predictions to [1, 5].
7. `recommend` ranks only movies the user has not rated; users with no history get the popularity ranking.
8. Write `docs/models.md` with equations, parameters, and edge-case behaviour.
9. Unit tests using a tiny hand-made matrix whose expected predictions are computed by hand.

## Acceptance criteria
- [ ] All four models implement the common interface.
- [ ] Hand-computed expected values match the code for similarity and prediction on the toy matrix (tolerance 1e-6).
- [ ] A test proves `fit` on a modified test partition gives identical results (models never see held-out data).
- [ ] Tests cover: zero denominator, user with 1 rating, unknown user, unknown item, item with no raters, k larger than available neighbours.
- [ ] No prediction outside [1, 5]; no already-rated movie in `recommend` output (tests).
- [ ] No dense full user-item matrix is built for similarity on the full dataset without justification.
- [ ] `pytest` passes with 0 failures (observed output).
- [ ] No hyperparameter tuning and no final metric table in this phase.

## Audit checklist
Re-derive one prediction by hand from `docs/models.md`; confirm code matches the equations; grep for any use of test data inside `fit`; run all tests.
