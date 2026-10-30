"""
Training, Model Selection, and Final Evaluation Pipeline for MovieRec Version 2.
Trains TruncatedSVD (k=30, seed=42) and Damped Popularity (m=50.0) on MovieLens 1M.
Validates models, performs model selection on Validation NDCG@10, and conducts one-shot Test evaluation.
"""

import json
import os
import sys
import time
from typing import Dict

# Ensure v2/backend is in sys.path
V2_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if V2_BACKEND_DIR not in sys.path:
    sys.path.insert(0, V2_BACKEND_DIR)

import pandas as pd
from app.ml.dataset import get_default_processed_dir
from app.ml.models.svd import TruncatedSVDRecommender
from app.ml.models.popularity import PopularityBaseline
from app.ml.evaluation import evaluate_recommender


def run_training_and_evaluation() -> Dict:
    proc_dir = get_default_processed_dir()
    base_v2_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    artifacts_dir = os.path.join(base_v2_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    print("[V2 ML Pipeline] Loading processed data splits...", flush=True)
    t0 = time.perf_counter()
    train_df = pd.read_csv(os.path.join(proc_dir, "train_ratings.csv.gz"), compression="gzip")
    val_df = pd.read_csv(os.path.join(proc_dir, "val_ratings.csv.gz"), compression="gzip")
    test_df = pd.read_csv(os.path.join(proc_dir, "test_ratings.csv.gz"), compression="gzip")
    print(f"  • Data loaded in {time.perf_counter() - t0:.2f}s (Train: {len(train_df):,}, Val: {len(val_df):,}, Test: {len(test_df):,})", flush=True)

    # --------------------------------------------------------------------------
    # Step 1: Model Fitting on Train Partition (597,742 ratings)
    # --------------------------------------------------------------------------
    print("\n[V2 ML Pipeline] 1. Fitting TruncatedSVD (k=30, random_state=42)...", flush=True)
    t_svd_start = time.perf_counter()
    svd_model = TruncatedSVDRecommender(n_factors=30, random_state=42).fit(train_df)
    svd_fit_time = time.perf_counter() - t_svd_start
    print(f"  • TruncatedSVD fitted in {svd_fit_time:.2f}s", flush=True)

    print("\n[V2 ML Pipeline] 2. Fitting PopularityBaseline (damping=50.0)...", flush=True)
    t_pop_start = time.perf_counter()
    pop_model = PopularityBaseline(damping=50.0).fit(train_df)
    pop_fit_time = time.perf_counter() - t_pop_start
    print(f"  • PopularityBaseline fitted in {pop_fit_time:.2f}s", flush=True)

    # --------------------------------------------------------------------------
    # Step 2: Evaluation on Validation Split for Model Selection
    # --------------------------------------------------------------------------
    print("\n[V2 ML Pipeline] 3. Evaluating models on VALIDATION partition (197,656 ratings)...", flush=True)
    print("  • Relevance threshold for NDCG@10 & MAP@10: rating >= 4.0", flush=True)

    t_val_svd = time.perf_counter()
    val_metrics_svd = evaluate_recommender(svd_model, val_df, k=10, relevance_threshold=4.0)
    print(f"  -> SVD Validation Metrics ({time.perf_counter() - t_val_svd:.2f}s): {val_metrics_svd}", flush=True)

    t_val_pop = time.perf_counter()
    val_metrics_pop = evaluate_recommender(pop_model, val_df, k=10, relevance_threshold=4.0)
    print(f"  -> Popularity Validation Metrics ({time.perf_counter() - t_val_pop:.2f}s): {val_metrics_pop}", flush=True)

    # Model Selection Rule: Higher NDCG@10 on Validation split
    if val_metrics_svd["NDCG@10"] > val_metrics_pop["NDCG@10"]:
        winner_name = "TruncatedSVDRecommender(k=30)"
        winner_model = svd_model
        print(f"\n[Model Selection] WINNER: {winner_name} (Val NDCG@10: {val_metrics_svd['NDCG@10']:.4f} vs Pop: {val_metrics_pop['NDCG@10']:.4f})")
    else:
        winner_name = "PopularityBaseline(damping=50.0)"
        winner_model = pop_model
        print(f"\n[Model Selection] WINNER: {winner_name}")

    # --------------------------------------------------------------------------
    # Step 3: One-Shot Final Evaluation on Held-Out Test Partition (204,811 ratings)
    # --------------------------------------------------------------------------
    print("\n[V2 ML Pipeline] 4. Evaluating WINNER on HELD-OUT TEST partition (204,811 ratings)...")
    t_test = time.perf_counter()
    test_metrics_svd = evaluate_recommender(svd_model, test_df, k=10, relevance_threshold=4.0)
    test_metrics_pop = evaluate_recommender(pop_model, test_df, k=10, relevance_threshold=4.0)
    print(f"  -> SVD Test Metrics ({time.perf_counter() - t_test:.2f}s): {test_metrics_svd}")
    print(f"  -> Popularity Test Metrics: {test_metrics_pop}")

    # --------------------------------------------------------------------------
    # Step 4: Export Artifacts & Metadata Exclusively into v2/backend/artifacts/
    # --------------------------------------------------------------------------
    print("\n[V2 ML Pipeline] 5. Exporting V2 model artifacts...")
    svd_artifact_path = os.path.join(artifacts_dir, "svd_1m_artifacts.npz")
    svd_model.save_artifacts(svd_artifact_path)
    print(f"  • Saved SVD artifact ({os.path.getsize(svd_artifact_path):,} bytes) -> {svd_artifact_path}")

    pop_artifact_path = os.path.join(artifacts_dir, "popularity_1m_artifacts.json")
    pop_data = {
        "damping": pop_model.damping,
        "global_mean": pop_model.global_mean,
        "min_ratings": pop_model.min_ratings,
        "damped_scores": {int(k): round(float(v), 4) for k, v in pop_model.damped_scores.items()},
        "item_counts": {int(k): int(v) for k, v in pop_model.item_counts.items()},
    }
    with open(pop_artifact_path, "w", encoding="utf-8") as f:
        json.dump(pop_data, f, indent=2)
    print(f"  • Saved Popularity artifact ({os.path.getsize(pop_artifact_path):,} bytes) -> {pop_artifact_path}")

    # Save summary report
    summary_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset": "MovieLens 1M (ml-1m)",
        "train_ratings": len(train_df),
        "val_ratings": len(val_df),
        "test_ratings": len(test_df),
        "relevance_threshold": 4.0,
        "evaluation_protocol": "Chronological per-user split (60/20/20); candidate space all unrated catalog items; IDCG with top-k relevant items",
        "models": {
            "TruncatedSVD": {
                "n_factors": 30,
                "random_state": 42,
                "fit_time_seconds": round(svd_fit_time, 2),
                "validation_metrics": val_metrics_svd,
                "test_metrics": test_metrics_svd,
            },
            "PopularityBaseline": {
                "damping": 50.0,
                "fit_time_seconds": round(pop_fit_time, 2),
                "validation_metrics": val_metrics_pop,
                "test_metrics": test_metrics_pop,
            },
        },
        "model_selection": {
            "criterion": "Validation NDCG@10",
            "winner": winner_name,
            "svd_val_ndcg": val_metrics_svd["NDCG@10"],
            "popularity_val_ndcg": val_metrics_pop["NDCG@10"],
        },
    }

    report_path = os.path.join(artifacts_dir, "evaluation_metrics.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)
    print(f"  • Exported evaluation metrics JSON -> {report_path}")

    # Export CSV summary
    csv_rows = [
        {
            "model": "TruncatedSVDRecommender",
            "hyperparameters": "k=30, random_state=42",
            "val_ndcg@10": val_metrics_svd["NDCG@10"],
            "val_map@10": val_metrics_svd["MAP@10"],
            "val_rmse": val_metrics_svd["RMSE"],
            "test_ndcg@10": test_metrics_svd["NDCG@10"],
            "test_map@10": test_metrics_svd["MAP@10"],
            "test_rmse": test_metrics_svd["RMSE"],
            "fit_time_sec": round(svd_fit_time, 2),
        },
        {
            "model": "PopularityBaseline",
            "hyperparameters": "damping=50.0",
            "val_ndcg@10": val_metrics_pop["NDCG@10"],
            "val_map@10": val_metrics_pop["MAP@10"],
            "val_rmse": val_metrics_pop["RMSE"],
            "test_ndcg@10": test_metrics_pop["NDCG@10"],
            "test_map@10": test_metrics_pop["MAP@10"],
            "test_rmse": test_metrics_pop["RMSE"],
            "fit_time_sec": round(pop_fit_time, 2),
        },
    ]
    pd.DataFrame(csv_rows).to_csv(os.path.join(artifacts_dir, "model_comparison.csv"), index=False)
    print(f"  • Exported model comparison CSV -> {os.path.join(artifacts_dir, 'model_comparison.csv')}")

    return summary_report


if __name__ == "__main__":
    run_training_and_evaluation()
