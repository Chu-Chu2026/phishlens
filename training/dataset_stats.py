"""Generate dataset statistics for analytics page."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from streamlit_app.utils.feature_extraction import FEATURE_NAMES, extract_features_dataframe
from training.config import EVAL_DIR, PROCESSED_DIR

logger = logging.getLogger(__name__)


def generate_dataset_stats(output_path: Path | None = None) -> dict:
    """
    Compute dataset overview statistics and feature distributions.

    Returns:
        Dictionary with class balance, feature means per class, and sources.
    """
    output_path = output_path or EVAL_DIR / "dataset_stats.json"
    df = pd.read_csv(PROCESSED_DIR / "full.csv")

    features = extract_features_dataframe(df["url"].tolist())
    features["label"] = df["label"].values

    # Normalize feature means to 0-1 for visualization
    feature_distributions = []
    key_features = [
        "url_length", "num_hyphens", "has_https", "subdomain_count",
        "suspicious_keyword_count", "is_suspicious_tld", "hostname_entropy",
    ]
    for feat in key_features:
        if feat not in features.columns:
            continue
        col = features[feat]
        max_val = col.max() or 1.0
        phish_mean = float(features[features["label"] == 1][feat].mean() / max_val)
        legit_mean = float(features[features["label"] == 0][feat].mean() / max_val)
        feature_distributions.append({
            "name": feat,
            "phishing": round(phish_mean, 3),
            "legitimate": round(legit_mean, 3),
        })

    stats = {
        "total_urls": len(df),
        "phishing_count": int((df["label"] == 1).sum()),
        "legitimate_count": int((df["label"] == 0).sum()),
        "feature_count": len(FEATURE_NAMES),
        "feature_distributions": feature_distributions,
        "sources": df["source"].value_counts().to_dict() if "source" in df.columns else {},
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    logger.info("Dataset stats saved to %s", output_path)
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_dataset_stats()
