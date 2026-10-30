"""
Orchestration script for Phase 3:
- Validation hyperparameter tuning across all 4 models.
- Pre-committed model selection based on Validation NDCG@10 (RMSE secondary).
- Final test evaluation via --final flag (refit on train+validation, evaluated once on test).
- Cold-start experiment (interaction truncation to 1, 3, 5, 10 ratings).
- Comprehensive result logging to results/ CSVs and visualization plots.
"""

import argparse
from datetime import datetime
import os
import sys
from typing import Dict, List, Optional, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.recsys.data import load_ratings, get_default_data_dir
from src.recsys.split import chronological_split
from src.recsys.models.popularity import PopularityBaseline
from src.recsys.models.user_knn import UserKNNRecommender
from src.recsys.models.item_knn import ItemKNNRecommender
from src.recsys.models.svd import TruncatedSVDRecommender
from src.recsys.evaluation import evaluate_model

RESULTS_DIR = os.path.join(BASE_DIR, "results")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")
FINAL_LOG_PATH = os.path.join(RESULTS_DIR, "final_run.log")


def log_final_run(info: str) -> int:
    """Log an execution of the final test run and return the cumulative run count."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    count = 1
    if os.path.exists(FINAL_LOG_PATH):
        with open(FINAL_LOG_PATH, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("RUN_INDEX:"):
                    count += 1

    with open(FINAL_LOG_PATH, "a") as f:
        timestamp = datetime.now().isoformat()
        f.write(f"RUN_INDEX: {count} | TIMESTAMP: {timestamp} | INFO: {info}\n")
    return count


def extract_best_configs(df_tuning: pd.DataFrame) -> Dict[str, dict]:
    """Extract best configuration per model family by validation NDCG@10 (RMSE secondary)."""
    best_configs = {}
    for model_name, grp in df_tuning.groupby("model"):
        sorted_grp = grp.sort_values(by=["ndcg@10", "rmse"], ascending=[False, True])
        best_row = sorted_grp.iloc[0].to_dict()
        best_configs[model_name] = best_row
        print(f"  Selected {model_name}: NDCG@10={best_row['ndcg@10']:.4f}, RMSE={best_row['rmse']:.4f}", flush=True)
    return best_configs


def run_validation_tuning(
    train: pd.DataFrame,
    val: pd.DataFrame,
    sample_users: Optional[int] = 150,
) -> Tuple[pd.DataFrame, Dict[str, dict]]:
    """
    Search hyperparameters on validation partition ONLY.
    Never touches test partition.
    """
    print("\n--- Running Validation Hyperparameter Tuning (Validation Partition Only) ---", flush=True)
    tuning_records = []

    val_users = sorted(val["user_id"].unique())
    if sample_users and len(val_users) > sample_users:
        np.random.seed(42)
        eval_u = set(np.random.choice(val_users, size=sample_users, replace=False))
        val_sub = val[val["user_id"].isin(eval_u)].copy()
    else:
        val_sub = val

    # 1. Popularity Baseline Tuning
    print("Tuning Popularity Baseline...", flush=True)
    for damping in [0.0, 5.0, 10.0, 25.0, 50.0]:
        for min_ratings in [1, 5, 10]:
            model = PopularityBaseline(damping=damping, min_ratings=min_ratings).fit(train)
            metrics = evaluate_model(model, val_sub, train, k_values=(5, 10, 20))
            metrics.update({
                "model": "PopularityBaseline",
                "damping": damping,
                "min_ratings": min_ratings,
                "k": None,
                "min_overlap": None,
                "n_factors": None,
            })
            tuning_records.append(metrics)

    # 2. UserKNN Tuning
    print("Tuning User-based kNN...", flush=True)
    for k in [10, 20, 30]:
        for min_overlap in [1, 2]:
            model = UserKNNRecommender(k=k, min_overlap=min_overlap).fit(train)
            metrics = evaluate_model(model, val_sub, train, k_values=(5, 10, 20))
            metrics.update({
                "model": "UserKNNRecommender",
                "damping": None,
                "min_ratings": None,
                "k": k,
                "min_overlap": min_overlap,
                "n_factors": None,
            })
            tuning_records.append(metrics)

    # 3. ItemKNN Tuning
    print("Tuning Item-based kNN...", flush=True)
    for k in [10, 20, 30]:
        for min_overlap in [1, 2]:
            model = ItemKNNRecommender(k=k, min_overlap=min_overlap).fit(train)
            metrics = evaluate_model(model, val_sub, train, k_values=(5, 10, 20))
            metrics.update({
                "model": "ItemKNNRecommender",
                "damping": None,
                "min_ratings": None,
                "k": k,
                "min_overlap": min_overlap,
                "n_factors": None,
            })
            tuning_records.append(metrics)

    # 4. Truncated SVD Tuning
    print("Tuning Truncated SVD Benchmark...", flush=True)
    for n_factors in [5, 10, 20, 30, 50]:
        model = TruncatedSVDRecommender(n_factors=n_factors, random_state=42).fit(train)
        metrics = evaluate_model(model, val_sub, train, k_values=(5, 10, 20))
        metrics.update({
            "model": "TruncatedSVDRecommender",
            "damping": None,
            "min_ratings": None,
            "k": None,
            "min_overlap": None,
            "n_factors": n_factors,
        })
        tuning_records.append(metrics)

    df_tuning = pd.DataFrame(tuning_records)
    csv_path = os.path.join(RESULTS_DIR, "validation_tuning.csv")
    df_tuning.to_csv(csv_path, index=False)
    print(f"Validation tuning results saved to: {csv_path}", flush=True)

    best_configs = extract_best_configs(df_tuning)
    return df_tuning, best_configs


def run_cold_start_experiment(
    train: pd.DataFrame,
    val: pd.DataFrame,
    best_configs: Dict[str, dict],
    n_sample_users: int = 100,
    truncation_levels: Tuple[int, ...] = (1, 3, 5, 10),
) -> pd.DataFrame:
    """
    Cold-start experiment: truncates user training interaction histories to M items,
    measuring performance degradation across models.
    """
    print("\n--- Running Cold-Start Experiment ---", flush=True)
    np.random.seed(42)
    sample_users = np.random.choice(val["user_id"].unique(), size=n_sample_users, replace=False)
    val_sample = val[val["user_id"].isin(sample_users)].copy()

    records = []
    for m in truncation_levels:
        print(f"Evaluating truncation level M={m} ratings...", flush=True)
        truncated_rows = []
        for u in sample_users:
            u_train = train[train["user_id"] == u].sort_values("timestamp")
            truncated_rows.append(u_train.iloc[:m])

        other_train = train[~train["user_id"].isin(sample_users)]
        truncated_train = pd.concat([other_train] + truncated_rows, ignore_index=True)

        pop = PopularityBaseline(
            damping=best_configs["PopularityBaseline"]["damping"],
            min_ratings=int(best_configs["PopularityBaseline"]["min_ratings"]),
        ).fit(truncated_train)

        u_knn = UserKNNRecommender(
            k=int(best_configs["UserKNNRecommender"]["k"]),
            min_overlap=int(best_configs["UserKNNRecommender"]["min_overlap"]),
        ).fit(truncated_train)

        i_knn = ItemKNNRecommender(
            k=int(best_configs["ItemKNNRecommender"]["k"]),
            min_overlap=int(best_configs["ItemKNNRecommender"]["min_overlap"]),
        ).fit(truncated_train)

        svd = TruncatedSVDRecommender(
            n_factors=int(best_configs["TruncatedSVDRecommender"]["n_factors"]),
            random_state=42,
        ).fit(truncated_train)

        models = [
            ("PopularityBaseline", pop),
            ("UserKNNRecommender", u_knn),
            ("ItemKNNRecommender", i_knn),
            ("TruncatedSVDRecommender", svd),
        ]

        for name, model in models:
            res = evaluate_model(model, val_sample, truncated_train, k_values=(10,))
            records.append({
                "truncation_m": m,
                "model": name,
                "ndcg@10": res["ndcg@10"],
                "recall@10": res["recall@10"],
                "rmse": res["rmse"],
            })

    df_cold = pd.DataFrame(records)
    csv_path = os.path.join(RESULTS_DIR, "cold_start_experiment.csv")
    df_cold.to_csv(csv_path, index=False)
    print(f"Cold-start experiment saved to: {csv_path}", flush=True)
    return df_cold


def run_final_test_evaluation(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    best_configs: Dict[str, dict],
) -> pd.DataFrame:
    """
    Final Test Run:
    Refits selected configurations on Train + Validation,
    then evaluates on the held-out Test set ONCE.
    """
    print("\n--- Executing Final Test Set Evaluation (--final) ---", flush=True)
    run_count = log_final_run(f"Final evaluation run on ml-100k test set with {len(test)} test ratings.")
    print(f"Logged to {FINAL_LOG_PATH} (Cumulative execution count: {run_count})", flush=True)

    train_val = pd.concat([train, val], ignore_index=True)
    catalog_items = set(train_val["item_id"]).union(set(test["item_id"]))

    test_records = []

    # 1. Popularity Baseline
    print("Evaluating final Popularity Baseline on Test...", flush=True)
    pop = PopularityBaseline(
        damping=best_configs["PopularityBaseline"]["damping"],
        min_ratings=int(best_configs["PopularityBaseline"]["min_ratings"]),
    ).fit(train_val)
    pop_res = evaluate_model(pop, test, train_val, catalog_items=catalog_items, k_values=(5, 10, 20))
    pop_res["model"] = "PopularityBaseline"
    pop_res["config"] = f"damping={best_configs['PopularityBaseline']['damping']}, min_ratings={best_configs['PopularityBaseline']['min_ratings']}"
    test_records.append(pop_res)

    # 2. UserKNN
    print("Evaluating final User-based kNN on Test...", flush=True)
    u_knn = UserKNNRecommender(
        k=int(best_configs["UserKNNRecommender"]["k"]),
        min_overlap=int(best_configs["UserKNNRecommender"]["min_overlap"]),
    ).fit(train_val)
    u_res = evaluate_model(u_knn, test, train_val, catalog_items=catalog_items, k_values=(5, 10, 20))
    u_res["model"] = "UserKNNRecommender"
    u_res["config"] = f"k={best_configs['UserKNNRecommender']['k']}, min_overlap={best_configs['UserKNNRecommender']['min_overlap']}"
    test_records.append(u_res)

    # 3. ItemKNN
    print("Evaluating final Item-based kNN on Test...", flush=True)
    i_knn = ItemKNNRecommender(
        k=int(best_configs["ItemKNNRecommender"]["k"]),
        min_overlap=int(best_configs["ItemKNNRecommender"]["min_overlap"]),
    ).fit(train_val)
    i_res = evaluate_model(i_knn, test, train_val, catalog_items=catalog_items, k_values=(5, 10, 20))
    i_res["model"] = "ItemKNNRecommender"
    i_res["config"] = f"k={best_configs['ItemKNNRecommender']['k']}, min_overlap={best_configs['ItemKNNRecommender']['min_overlap']}"
    test_records.append(i_res)

    # 4. Truncated SVD
    print("Evaluating final Truncated SVD Benchmark on Test...", flush=True)
    svd = TruncatedSVDRecommender(
        n_factors=int(best_configs["TruncatedSVDRecommender"]["n_factors"]),
        random_state=42,
    ).fit(train_val)
    svd_res = evaluate_model(svd, test, train_val, catalog_items=catalog_items, k_values=(5, 10, 20))
    svd_res["model"] = "TruncatedSVDRecommender"
    svd_res["config"] = f"n_factors={best_configs['TruncatedSVDRecommender']['n_factors']}, seed=42"
    test_records.append(svd_res)

    df_test = pd.DataFrame(test_records)
    csv_path = os.path.join(RESULTS_DIR, "test_evaluation_results.csv")
    df_test.to_csv(csv_path, index=False)
    print(f"Final test evaluation results saved to: {csv_path}", flush=True)

    display_cols = ["model", "ndcg@10", "precision@10", "recall@10", "rmse", "mae", "coverage@10", "novelty@10"]
    print("\n=== FINAL TEST EVALUATION RESULTS ===", flush=True)
    print(df_test[display_cols].to_string(index=False), flush=True)

    return df_test


def generate_evaluation_plots(df_test: pd.DataFrame, df_cold: pd.DataFrame) -> None:
    """Generate and save publication-quality evaluation comparison figures."""
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. NDCG@10 Model Comparison Bar Chart
    fig, ax = plt.subplots(figsize=(8, 5))
    models = df_test["model"]
    ndcg10_scores = df_test["ndcg@10"]
    colors = ["#7f7f7f", "#1f77b4", "#ff7f0e", "#2ca02c"]
    bars = ax.bar(models, ndcg10_scores, color=colors, edgecolor="black", width=0.5)
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.4f}", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 4),
                    textcoords="offset points", ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_title("Test Set NDCG@10 Comparison across Models", fontsize=14, fontweight="bold")
    ax.set_ylabel("NDCG@10", fontsize=12)
    ax.set_ylim(0, max(ndcg10_scores) * 1.18)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "model_comparison_ndcg10.png"), dpi=200)
    plt.close(fig)

    # 2. Cold-Start Sensitivity Curve
    fig, ax = plt.subplots(figsize=(8, 5))
    model_styles = {
        "PopularityBaseline": ("#7f7f7f", "--", "o"),
        "UserKNNRecommender": ("#1f77b4", "-", "s"),
        "ItemKNNRecommender": ("#ff7f0e", "-", "^"),
        "TruncatedSVDRecommender": ("#2ca02c", "-", "D"),
    }
    for model_name, grp in df_cold.groupby("model"):
        color, ls, marker = model_styles.get(model_name, ("black", "-", "o"))
        ax.plot(grp["truncation_m"], grp["ndcg@10"], label=model_name, color=color, linestyle=ls, marker=marker, linewidth=2)

    ax.set_title("Cold-Start Robustness (NDCG@10 vs. Training Ratings M)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Available Training Ratings (M)", fontsize=12)
    ax.set_ylabel("NDCG@10", fontsize=12)
    ax.set_xticks([1, 3, 5, 10])
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "cold_start_curve.png"), dpi=200)
    plt.close(fig)

    print(f"Evaluation plots saved to: {PLOTS_DIR}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Evaluate collaborative filtering models.")
    parser.add_argument("--final", action="store_true", help="Execute the final test partition evaluation once.")
    parser.add_argument("--sample-val", type=int, default=150, help="Number of validation users to sample for fast ranking sweeps.")
    parser.add_argument("--force-retune", action="store_true", help="Force re-running validation tuning even if tuning CSV exists.")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)

    print("Loading MovieLens 100K ratings...", flush=True)
    ratings = load_ratings(get_default_data_dir())
    splits = chronological_split(ratings, train_frac=0.60, val_frac=0.20, random_state=42)

    # 1. Validation Tuning (Reuse existing completed results if present, unless forced)
    tuning_csv = os.path.join(RESULTS_DIR, "validation_tuning.csv")
    if os.path.exists(tuning_csv) and not args.force_retune:
        print(f"Loading existing completed validation tuning results from {tuning_csv}...", flush=True)
        df_tuning = pd.read_csv(tuning_csv)
        print("Extracting fixed selected configurations from validation tuning:", flush=True)
        best_configs = extract_best_configs(df_tuning)
    else:
        df_tuning, best_configs = run_validation_tuning(splits.train, splits.val, sample_users=args.sample_val)

    # 2. Cold-Start Experiment (Reuse existing completed results if present)
    cold_csv = os.path.join(RESULTS_DIR, "cold_start_experiment.csv")
    if os.path.exists(cold_csv) and not args.force_retune:
        print(f"Loading existing completed cold-start experiment results from {cold_csv}...", flush=True)
        df_cold = pd.read_csv(cold_csv)
    else:
        df_cold = run_cold_start_experiment(splits.train, splits.val, best_configs, n_sample_users=80)

    # 3. Final Test Run (if authorized via --final flag)
    if args.final:
        df_test = run_final_test_evaluation(splits.train, splits.val, splits.test, best_configs)
        generate_evaluation_plots(df_test, df_cold)
    else:
        print("\nNOTE: --final flag not provided. Skipping final test evaluation to prevent test snooping.", flush=True)


if __name__ == "__main__":
    main()
