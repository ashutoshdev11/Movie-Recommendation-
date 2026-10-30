"""
Evaluation Metrics & Protocol for MovieRec Version 2 (MovieLens 1M).
Implements NDCG@K, MAP@K, and RMSE with explicit relevance threshold documentation.
"""

from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd


def compute_rmse(actuals: np.ndarray, predictions: np.ndarray) -> float:
    """Root Mean Squared Error."""
    if len(actuals) == 0:
        return 0.0
    return float(np.sqrt(np.mean((actuals - predictions) ** 2)))


def compute_dcg_at_k(relevance_scores: List[float], k: int = 10) -> float:
    """
    Discounted Cumulative Gain with exponential gain formula:
        DCG@K = sum_{i=1}^K (2^rel_i - 1) / log2(i + 1)
    """
    dcg = 0.0
    for i, rel in enumerate(relevance_scores[:k], start=1):
        if rel > 0:
            dcg += (2.0 ** rel - 1.0) / np.log2(i + 1)
    return float(dcg)


def compute_ndcg_at_k(
    actual_items: Dict[int, float],
    recommended_items: List[int],
    k: int = 10,
    relevance_threshold: float = 4.0,
) -> float:
    """
    Normalized Discounted Cumulative Gain at rank K.
    
    Relevance Definition:
        Linear gain using actual rating if rating >= relevance_threshold (default 4.0), else 0.
        
    Args:
        actual_items: Dict mapping item_id -> ground truth rating in test/val set.
        recommended_items: Ordered list of recommended item_ids.
        k: Cutoff rank (default 10).
        relevance_threshold: Rating threshold for positive relevance (default 4.0).
    """
    # Filter to relevant ground truth items
    relevant_actuals = {i: r for i, r in actual_items.items() if r >= relevance_threshold}
    if not relevant_actuals:
        return 0.0

    # Realized relevance at each rank
    rel_realized = [actual_items.get(item_id, 0.0) if actual_items.get(item_id, 0.0) >= relevance_threshold else 0.0 for item_id in recommended_items[:k]]
    dcg = compute_dcg_at_k(rel_realized, k=k)

    # Ideal DCG: sort all ground truth ratings descending
    ideal_ratings = sorted(list(relevant_actuals.values()), reverse=True)[:k]
    idcg = compute_dcg_at_k(ideal_ratings, k=k)

    if idcg <= 0.0:
        return 0.0
    return float(dcg / idcg)


def compute_map_at_k(
    actual_items: Dict[int, float],
    recommended_items: List[int],
    k: int = 10,
    relevance_threshold: float = 4.0,
) -> float:
    """
    Mean Average Precision at rank K (AP@K for a single user).
    
    Formula:
        AP@K = (1 / min(K, |R_u|)) * sum_{i=1}^K P(i) * I(item_i is relevant)
        where P(i) = (relevant items up to i) / i
        
    Args:
        actual_items: Dict mapping item_id -> rating in test/val partition.
        recommended_items: List of recommended item_ids.
        k: Cutoff rank (default 10).
        relevance_threshold: Positive relevance cutoff (r >= 4.0).
    """
    relevant_set = {i for i, r in actual_items.items() if r >= relevance_threshold}
    if not relevant_set:
        return 0.0

    num_relevant_hits = 0
    score_sum = 0.0

    for i, item_id in enumerate(recommended_items[:k], start=1):
        if item_id in relevant_set:
            num_relevant_hits += 1
            precision_at_i = num_relevant_hits / i
            score_sum += precision_at_i

    denominator = min(k, len(relevant_set))
    return float(score_sum / denominator) if denominator > 0 else 0.0


def evaluate_recommender(
    model,
    eval_df: pd.DataFrame,
    k: int = 10,
    relevance_threshold: float = 4.0,
    batch_users: Optional[List[int]] = None,
) -> Dict[str, float]:
    """
    Comprehensive evaluation across an entire evaluation split (Validation or Test).
    
    Computes:
        - NDCG@K
        - MAP@K
        - RMSE
    """
    # 1. Rating Prediction Error (RMSE)
    u_arr = eval_df["user_id"].to_numpy(dtype=np.int64)
    m_arr = eval_df["movie_id"].to_numpy(dtype=np.int64)
    actuals_arr = eval_df["rating"].to_numpy(dtype=np.float64)

    preds_arr = np.empty(len(actuals_arr), dtype=np.float64)
    predict_fn = model.predict
    for i in range(len(actuals_arr)):
        preds_arr[i] = predict_fn(int(u_arr[i]), int(m_arr[i]))

    rmse = compute_rmse(actuals_arr, preds_arr)

    # 2. Ranking Metrics (NDCG@K and MAP@K)
    eval_user_items: Dict[int, Dict[int, float]] = {}
    for uid, grp in eval_df.groupby("user_id"):
        eval_user_items[int(uid)] = dict(zip(grp["movie_id"], grp["rating"]))

    eval_users = batch_users if batch_users is not None else sorted(eval_user_items.keys())
    
    ndcg_list = []
    map_list = []

    for uid in eval_users:
        user_ground_truth = eval_user_items.get(uid, {})
        # Check if user has any relevant items in eval split
        has_relevant = any(r >= relevance_threshold for r in user_ground_truth.values())
        if not has_relevant:
            continue

        raw_recs = model.recommend(uid, n=k, exclude_seen=True)
        recommended_ids = [it for it, _ in raw_recs]

        ndcg = compute_ndcg_at_k(user_ground_truth, recommended_ids, k=k, relevance_threshold=relevance_threshold)
        ap = compute_map_at_k(user_ground_truth, recommended_ids, k=k, relevance_threshold=relevance_threshold)

        ndcg_list.append(ndcg)
        map_list.append(ap)

    mean_ndcg = float(np.mean(ndcg_list)) if ndcg_list else 0.0
    mean_map = float(np.mean(map_list)) if map_list else 0.0

    return {
        f"NDCG@{k}": round(mean_ndcg, 4),
        f"MAP@{k}": round(mean_map, 4),
        "RMSE": round(float(rmse), 4),
        "evaluated_users": len(ndcg_list),
        "total_eval_interactions": len(eval_df),
    }
