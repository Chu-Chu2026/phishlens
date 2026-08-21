"""Generate SHAP explainability artifacts."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from streamlit_app.utils.feature_extraction import FEATURE_NAMES, extract_features_dataframe
from training.config import (
    EVAL_DIR,
    MODELS_DIR,
    PROCESSED_DIR,
    RANDOM_STATE,
    SHAP_BACKGROUND_SIZE,
    SHAP_DIR,
    SHAP_TEST_SAMPLE_SIZE,
)

logger = logging.getLogger(__name__)


def _get_tree_model(model):
    """Extract a tree-based model suitable for TreeExplainer."""
    # VotingClassifier — prefer the Random Forest estimator for TreeExplainer.
    if hasattr(model, "named_estimators_") and "random_forest" in model.named_estimators_:
        return model.named_estimators_["random_forest"]
    if hasattr(model, "estimators_"):
        for estimator in model.estimators_:
            if estimator.__class__.__name__ == "RandomForestClassifier":
                return estimator
    return model


def generate_shap_artifacts(output_dir: Path | None = None) -> dict:
    """
    Precompute global SHAP values and save summary plots.

    Returns:
        Metadata about generated SHAP artifacts.
    """
    output_dir = output_dir or SHAP_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    ensemble = joblib.load(MODELS_DIR / "ensemble.joblib")
    tree_model = _get_tree_model(ensemble)

    train_df = pd.read_csv(PROCESSED_DIR / "train.csv")
    test_df = pd.read_csv(PROCESSED_DIR / "test.csv")

    # Background sample for explainer
    bg_urls = train_df["url"].sample(
        min(SHAP_BACKGROUND_SIZE, len(train_df)), random_state=RANDOM_STATE
    ).tolist()
    X_bg = extract_features_dataframe(bg_urls)

    # Test sample for global SHAP
    test_sample = test_df.sample(
        min(SHAP_TEST_SAMPLE_SIZE, len(test_df)), random_state=RANDOM_STATE
    )
    X_test = extract_features_dataframe(test_sample["url"].tolist())

    explainer = shap.TreeExplainer(tree_model)
    shap_values = explainer.shap_values(X_test)

    # Normalize SHAP output shape for binary classification
    if isinstance(shap_values, list):
        sv = np.asarray(shap_values[1])
    else:
        sv = np.asarray(shap_values)

    if sv.ndim == 3:
        sv = sv[:, :, 1]

    mean_abs = np.abs(sv).mean(axis=0).flatten()
    if len(mean_abs) != len(FEATURE_NAMES):
        mean_abs = mean_abs[: len(FEATURE_NAMES)]

    # Global importance (mean |SHAP|)
    importance = pd.DataFrame({
        "feature": FEATURE_NAMES[: len(mean_abs)],
        "mean_abs_shap": mean_abs,
    }).sort_values("mean_abs_shap", ascending=False)

    importance_dict = importance.to_dict(orient="records")
    (output_dir / "global_importance.json").write_text(
        json.dumps(importance_dict, indent=2), encoding="utf-8"
    )

    # Summary plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(sv, X_test, feature_names=FEATURE_NAMES, show=False, max_display=15)
    plt.tight_layout()
    plt.savefig(output_dir / "summary_plot.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Bar plot (mean |SHAP|)
    plt.figure(figsize=(10, 6))
    shap.summary_plot(sv, X_test, feature_names=FEATURE_NAMES, plot_type="bar", show=False, max_display=15)
    plt.tight_layout()
    plt.savefig(output_dir / "importance_bar.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Save background data for local explanations
    joblib.dump({"X_bg": X_bg, "feature_names": FEATURE_NAMES}, output_dir / "background.joblib")

    metadata = {
        "explainer_type": "TreeExplainer",
        "base_model": type(tree_model).__name__,
        "background_size": len(X_bg),
        "test_sample_size": len(X_test),
        "top_features": importance_dict[:10],
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("SHAP artifacts saved to %s", output_dir)
    return metadata


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_shap_artifacts()
