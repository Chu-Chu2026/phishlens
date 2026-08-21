"""Preprocess raw URL dataset: clean, deduplicate, and stratified split."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from training.config import (
    PROCESSED_DIR,
    RANDOM_STATE,
    RAW_DIR,
    TEST_RATIO,
    TRAIN_RATIO,
    VAL_RATIO,
)
from training.download_data import download_all

logger = logging.getLogger(__name__)


def _clean_urls(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and deduplicate URL records."""
    df = df.copy()
    df["url"] = df["url"].astype(str).str.strip()
    df = df[df["url"].str.len() > 5]
    df = df[df["url"].str.contains(r"\.", na=False)]
    df["label"] = df["label"].astype(int)
    df = df.drop_duplicates(subset=["url"], keep="first")
    df = df.reset_index(drop=True)
    return df


def preprocess(
    raw_path: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Load raw data, clean, and create stratified train/val/test splits.

    Returns:
        Dictionary with keys 'train', 'val', 'test', 'full'.
    """
    output_dir = output_dir or PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if raw_path and raw_path.exists():
        df = pd.read_csv(raw_path)
    else:
        merged = RAW_DIR / "merged_raw.csv"
        if merged.exists():
            df = pd.read_csv(merged)
        else:
            df = download_all()

    df = _clean_urls(df)
    logger.info("Cleaned dataset: %d URLs", len(df))

    # Stratified split: first train vs temp, then val vs test
    train_df, temp_df = train_test_split(
        df,
        test_size=(1 - TRAIN_RATIO),
        random_state=RANDOM_STATE,
        stratify=df["label"],
    )
    val_ratio_of_temp = VAL_RATIO / (VAL_RATIO + TEST_RATIO)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1 - val_ratio_of_temp),
        random_state=RANDOM_STATE,
        stratify=temp_df["label"],
    )

    splits = {"train": train_df, "val": val_df, "test": test_df, "full": df}
    for name, split_df in splits.items():
        path = output_dir / f"{name}.csv"
        split_df.to_csv(path, index=False)
        logger.info("Saved %s: %d rows", path, len(split_df))

    stats = {
        "total_urls": len(df),
        "phishing_count": int((df["label"] == 1).sum()),
        "legitimate_count": int((df["label"] == 0).sum()),
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "sources": df["source"].value_counts().to_dict() if "source" in df.columns else {},
        "random_state": RANDOM_STATE,
    }
    stats_path = output_dir / "dataset_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    logger.info("Dataset stats saved to %s", stats_path)

    return splits


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    preprocess()
