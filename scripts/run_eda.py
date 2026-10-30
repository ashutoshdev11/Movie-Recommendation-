"""
Exploratory Data Analysis (EDA) for MovieLens 100K.
Generates and saves at least 5 annotated figures to results/eda/.
"""

import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add src to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.recsys.data import load_ratings, load_movies, load_users, validate_dataset


def run_eda(output_dir: str = os.path.join(BASE_DIR, "results", "eda")) -> None:
    os.makedirs(output_dir, exist_ok=True)
    print("Loading datasets for EDA...")
    ratings = load_ratings()
    movies = load_movies()
    users = load_users()

    # Validate first
    report = validate_dataset(ratings, movies, users)
    print(report.summary)

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. User Activity Distribution (Ratings per User)
    print("Plotting User Activity Distribution...")
    user_counts = ratings["user_id"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(user_counts, bins=40, color="#1f77b4", edgecolor="black", alpha=0.8)
    ax.axvline(user_counts.median(), color="red", linestyle="--", label=f"Median ({int(user_counts.median())})")
    ax.axvline(user_counts.mean(), color="orange", linestyle=":", label=f"Mean ({user_counts.mean():.1f})")
    ax.set_title("User Activity Distribution (MovieLens 100K)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Ratings per User", fontsize=12)
    ax.set_ylabel("Count of Users", fontsize=12)
    ax.legend(fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "user_activity_distribution.png"), dpi=200)
    plt.close(fig)

    # 2. Movie Popularity (Long Tail)
    print("Plotting Movie Popularity Long Tail...")
    movie_counts = ratings["item_id"].value_counts().values
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(movie_counts) + 1), movie_counts, color="#2ca02c", linewidth=2)
    ax.fill_between(range(1, len(movie_counts) + 1), movie_counts, color="#2ca02c", alpha=0.2)
    ax.set_title("Movie Popularity: The Long Tail (MovieLens 100K)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Movie Rank (Ordered by Popularity)", fontsize=12)
    ax.set_ylabel("Number of Ratings Received", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "movie_popularity_long_tail.png"), dpi=200)
    plt.close(fig)

    # 3. Rating Distribution
    print("Plotting Rating Distribution...")
    rating_counts = ratings["rating"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(rating_counts.index, rating_counts.values, color="#9467bd", edgecolor="black", width=0.6)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:,}\n({height/len(ratings)*100:.1f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    ax.set_title("Overall Rating Distribution (1–5 Stars)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Star Rating", fontsize=12)
    ax.set_ylabel("Total Number of Ratings", fontsize=12)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_ylim(0, max(rating_counts.values) * 1.15)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "rating_distribution.png"), dpi=200)
    plt.close(fig)

    # 4. Matrix Sparsity Visualization
    print("Plotting Matrix Sparsity Breakdown...")
    fig, ax = plt.subplots(figsize=(6, 5))
    categories = ["Observed Ratings\n(6.30%)", "Missing Entries\n(93.70%)"]
    values = [len(ratings), (len(users) * len(movies)) - len(ratings)]
    colors = ["#1f77b4", "#d62728"]
    bars = ax.bar(categories, values, color=colors, edgecolor="black", width=0.5)
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(
            f"{val:,}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )
    ax.set_title("User-Item Interaction Sparsity (93.70%)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Number of Matrix Cells", fontsize=12)
    ax.set_ylim(0, max(values) * 1.15)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "matrix_sparsity.png"), dpi=200)
    plt.close(fig)

    # 5. Ratings Over Time (Temporal Volume)
    print("Plotting Ratings Over Time...")
    ratings["datetime"] = pd.to_datetime(ratings["timestamp"], unit="s")
    ratings_monthly = ratings.set_index("datetime").resample("ME").size()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(ratings_monthly.index, ratings_monthly.values, marker="o", color="#e377c2", linewidth=2)
    ax.set_title("Rating Volume Over Time (1997–1998)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Timeline (Month)", fontsize=12)
    ax.set_ylabel("Monthly Ratings Submitted", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "ratings_over_time.png"), dpi=200)
    plt.close(fig)

    print(f"All 5 EDA figures saved successfully to: {output_dir}")


if __name__ == "__main__":
    run_eda()
