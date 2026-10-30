"""
Per-user chronological dataset splitting for MovieLens 100K.
Follows the binding 60% train / 20% validation / 20% test protocol.
"""

from dataclasses import dataclass
import pandas as pd


@dataclass
class DatasetSplits:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame


def chronological_split(
    ratings: pd.DataFrame,
    train_frac: float = 0.60,
    val_frac: float = 0.20,
    random_state: int = 42,
) -> DatasetSplits:
    """
    Split ratings chronologically per user.
    - Each user's interactions are sorted by timestamp ascending.
    - Ties at boundary indices are broken deterministically using random_state.
    - Proportions: floor(train_frac * n_u) for train,
                   floor(val_frac * n_u) for val,
                   remainder for test.
    """
    if train_frac + val_frac >= 1.0:
        raise ValueError("train_frac + val_frac must be strictly less than 1.0")

    train_rows = []
    val_rows = []
    test_rows = []

    # Sort deterministically by user_id, timestamp, and a random tiebreaker column
    df = ratings.copy()
    # Add deterministic tie-breaker for identical timestamps
    rng = df.sample(frac=1.0, random_state=random_state).index
    df["_tie_breaker"] = rng

    # Group by user_id
    for user_id, group in df.groupby("user_id"):
        # Sort chronologically, breaking ties with _tie_breaker
        sorted_group = group.sort_values(by=["timestamp", "_tie_breaker"], ascending=[True, True])
        n_u = len(sorted_group)

        n_train = int(n_u * train_frac)
        n_val = int(n_u * val_frac)

        # Enforce that train gets at least 1 item if n_u >= 1
        if n_train == 0 and n_u > 0:
            n_train = 1

        u_train = sorted_group.iloc[:n_train]
        u_val = sorted_group.iloc[n_train : n_train + n_val]
        u_test = sorted_group.iloc[n_train + n_val :]

        train_rows.append(u_train)
        val_rows.append(u_val)
        test_rows.append(u_test)

    train_df = pd.concat(train_rows, ignore_index=True).drop(columns=["_tie_breaker"])
    val_df = pd.concat(val_rows, ignore_index=True).drop(columns=["_tie_breaker"])
    test_df = pd.concat(test_rows, ignore_index=True).drop(columns=["_tie_breaker"])

    return DatasetSplits(train=train_df, val=val_df, test=test_df)
