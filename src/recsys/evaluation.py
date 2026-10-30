"""
Evaluation metrics library for collaborative filtering recommendation systems.
Computes rating prediction metrics (MAE, RMSE), Top-K ranking metrics
(Precision@K, Recall@K, NDCG@K), Catalog Coverage@K, and Novelty@K.
"""

from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from src.recsys.models.base import BaseRecommender


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    if len(y_true) == 0:
        return 0.0
    return float(np.mean(np.abs(y_true - y_pred)))


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    if len(y_true) == 0:
        return 0.0
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def compute_dcg_at_k(hits: List[int], k: int) -> float:
    """
    Compute Discounted Cumulative Gain at rank K.
    hits: binary list where 1 indicates relevant item at that rank.
    Formula: sum_{m=1}^K (2^rel_m - 1) / log2(m + 1)
    """
    dcg = 0.0
    for m in range(min(len(hits), k)):
        if hits[m] == 1:
            dcg += 1.0 / np.log2(m + 2)  # m=0 -> rank 1 -> log2(2) = 1.0
    return float(dcg)


def compute_idcg_at_k(n_relevant: int, k: int) -> float:
    """Compute Ideal Discounted Cumulative Gain at rank K."""
    idcg = 0.0
    for m in range(min(n_relevant, k)):
        idcg += 1.0 / np.log2(m + 2)
    return float(idcg)


def compute_ndcg_at_k(recommended_items: List[int], relevant_items: Set[int], k: int) -> float:
    """Normalized Discounted Cumulative Gain at rank K."""
    if not relevant_items:
        return 0.0
    hits = [1 if item in relevant_items else 0 for item in recommended_items[:k]]
    dcg = compute_dcg_at_k(hits, k)
    idcg = compute_idcg_at_k(len(relevant_items), k)
    if idcg <= 0.0:
        return 0.0
    return float(dcg / idcg)


def compute_precision_at_k(recommended_items: List[int], relevant_items: Set[int], k: int) -> float:
    """Precision@K = |Rec_K cap Rel| / K."""
    if k <= 0:
        return 0.0
    rec_k = recommended_items[:k]
    hits = sum(1 for item in rec_k if item in relevant_items)
    return float(hits / k)


def compute_recall_at_k(recommended_items: List[int], relevant_items: Set[int], k: int) -> float:
    """Recall@K = |Rec_K cap Rel| / |Rel|."""
    if not relevant_items:
        return 0.0
    rec_k = recommended_items[:k]
    hits = sum(1 for item in rec_k if item in relevant_items)
    return float(hits / len(relevant_items))


def compute_coverage_at_k(
    all_recommendations: Dict[int, List[int]],
    catalog_items: Set[int],
    k: int,
) -> float:
    """Catalog Coverage@K = |bigcup Rec_K(u)| / |Catalog|."""
    if not catalog_items:
        return 0.0
    recommended_set: Set[int] = set()
    for recs in all_recommendations.values():
        recommended_set.update(recs[:k])
    return float(len(recommended_set) / len(catalog_items))


def compute_novelty_at_k(
    all_recommendations: Dict[int, List[int]],
    item_train_counts: Dict[int, int],
    n_train_users: int,
    total_catalog_size: int,
    k: int,
) -> float:
    """
    Novelty@K: Average self-information of recommendations using smoothed popularity:
    P(i) = (count(i) + 1) / (N_users + N_catalog)
    Self-information = -log2(P(i))
    """
    if not all_recommendations or k <= 0:
        return 0.0

    denom = float(n_train_users + total_catalog_size)
    total_self_info = 0.0
    total_count = 0

    for recs in all_recommendations.values():
        top_k = recs[:k]
        for item in top_k:
            count = item_train_counts.get(item, 0)
            p_i = (count + 1.0) / denom
            total_self_info += -np.log2(p_i)
            total_count += 1

    if total_count == 0:
        return 0.0
    return float(total_self_info / total_count)


def evaluate_model(
    model: BaseRecommender,
    eval_ratings: pd.DataFrame,
    train_ratings: pd.DataFrame,
    catalog_items: Optional[Set[int]] = None,
    k_values: Tuple[int, ...] = (5, 10, 20),
    relevance_threshold: float = 4.0,
    predict_batch_size: Optional[int] = None,
) -> Dict[str, float]:
    """
    Comprehensive evaluation of a fitted model on an evaluation partition (validation or test).
    Returns rating metrics (MAE, RMSE) and ranking metrics (Precision, Recall, NDCG @ 5, 10, 20),
    Catalog Coverage, Novelty, and count of excluded users without relevant test items.
    """
    if catalog_items is None:
        catalog_items = set(train_ratings["item_id"]).union(set(eval_ratings["item_id"]))

    # 1. Rating prediction metrics
    y_true = []
    y_pred = []
    for _, row in eval_ratings.iterrows():
        u = int(row["user_id"])
        i = int(row["item_id"])
        r = float(row["rating"])
        y_true.append(r)
        y_pred.append(model.predict(u, i))

    y_true_arr = np.array(y_true, dtype=np.float64)
    y_pred_arr = np.array(y_pred, dtype=np.float64)

    mae = compute_mae(y_true_arr, y_pred_arr)
    rmse = compute_rmse(y_true_arr, y_pred_arr)

    # 2. Ranking metrics
    # Group evaluation ground truth by user
    eval_user_ratings = eval_ratings.groupby("user_id")[["item_id", "rating"]].apply(
        lambda g: dict(zip(g["item_id"].astype(int), g["rating"].astype(float)))
    ).to_dict()

    max_k = max(k_values)
    all_recs: Dict[int, List[int]] = {}
    user_ranking_metrics: Dict[str, List[float]] = {
        f"ndcg@{k}": [] for k in k_values
    }
    for k in k_values:
        user_ranking_metrics[f"precision@{k}"] = []
        user_ranking_metrics[f"recall@{k}"] = []

    eval_users = sorted(eval_user_ratings.keys())
    excluded_users_count = 0

    for idx, u in enumerate(eval_users):
        if (idx + 1) % 200 == 0 or (idx + 1) == len(eval_users):
            print(f"  [{model.__class__.__name__}] Scored recommendations for {idx + 1}/{len(eval_users)} users...", flush=True)

        user_items = eval_user_ratings[u]
        relevant_items = {i for i, r in user_items.items() if r >= relevance_threshold}

        # Generate top max_k recommendations
        recs_with_scores = model.recommend(u, n=max_k, exclude_seen=True)
        rec_ids = [item_id for item_id, _ in recs_with_scores]
        all_recs[u] = rec_ids

        # If user has no relevant items, exclude from macro-averaging per protocol
        if not relevant_items:
            excluded_users_count += 1
            continue

        for k in k_values:
            ndcg_val = compute_ndcg_at_k(rec_ids, relevant_items, k)
            prec_val = compute_precision_at_k(rec_ids, relevant_items, k)
            rec_val = compute_recall_at_k(rec_ids, relevant_items, k)

            user_ranking_metrics[f"ndcg@{k}"].append(ndcg_val)
            user_ranking_metrics[f"precision@{k}"].append(prec_val)
            user_ranking_metrics[f"recall@{k}"].append(rec_val)

    # Summarize metrics
    results: Dict[str, float] = {
        "mae": float(mae),
        "rmse": float(rmse),
        "total_eval_users": len(eval_users),
        "evaluated_ranking_users": len(eval_users) - excluded_users_count,
        "excluded_users_no_relevant": excluded_users_count,
    }

    for metric_name, values in user_ranking_metrics.items():
        results[metric_name] = float(np.mean(values)) if values else 0.0

    # Coverage and Novelty
    item_train_counts = train_ratings["item_id"].value_counts().to_dict()
    n_train_users = train_ratings["user_id"].nunique()

    for k in k_values:
        cov_val = compute_coverage_at_k(all_recs, catalog_items, k)
        nov_val = compute_novelty_at_k(all_recs, item_train_counts, n_train_users, len(catalog_items), k)
        results[f"coverage@{k}"] = cov_val
        results[f"novelty@{k}"] = nov_val

    return results
