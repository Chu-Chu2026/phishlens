"""Train ensemble phishing URL classifier."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import f1_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from streamlit_app.utils.feature_extraction import (
    FEATURE_NAMES,
    extract_features_dataframe,
)
from training.config import MODELS_DIR, PROCESSED_DIR, RANDOM_STATE
from training.preprocess import preprocess

logger = logging.getLogger(__name__)


def _build_base_learners() -> dict:
    """Create untuned base learner instances."""
    return {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "svm": Pipeline([
            ("scaler", StandardScaler()),
            (
                "model",
                SVC(
                    kernel="rbf",
                    C=1.0,
                    probability=True,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]),
    }


def _build_ensemble(estimators: list[tuple[str, object]]) -> VotingClassifier:
    """Build soft-voting ensemble from fitted base learners."""
    return VotingClassifier(estimators=estimators, voting="soft", n_jobs=-1)


def _load_split_features(split_name: str) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """Load features and labels for a data split."""
    path = PROCESSED_DIR / f"{split_name}.csv"
    df = pd.read_csv(path)
    urls = df["url"].tolist()
    X = extract_features_dataframe(urls)
    y = df["label"].values
    return X, y, urls


def train(
    tune: bool = False,
    models_dir: Path | None = None,
) -> dict:
    """
    Train base learners and soft-voting ensemble.

    Args:
        tune: If True, run limited hyperparameter search on validation set.
        models_dir: Directory to save model artifacts.

    Returns:
        Training metadata dictionary.
    """
    models_dir = models_dir or MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    # Ensure processed data exists
    if not (PROCESSED_DIR / "train.csv").exists():
        preprocess()

    X_train, y_train, _ = _load_split_features("train")
    X_val, y_val, _ = _load_split_features("val")

    base_learners = _build_base_learners()
    fitted_estimators: list[tuple[str, object]] = []
    base_metrics: dict[str, dict] = {}

    for name, estimator in base_learners.items():
        logger.info("Training %s...", name)
        if tune and name == "random_forest":
            param_grid = {"n_estimators": [100, 200], "max_depth": [10, 20]}
            search = GridSearchCV(
                estimator,
                param_grid,
                cv=3,
                scoring="f1",
                n_jobs=-1,
            )
            search.fit(X_train, y_train)
            model = search.best_estimator_
            logger.info("Best RF params: %s", search.best_params_)
        else:
            model = estimator
            model.fit(X_train, y_train)

        val_pred = model.predict(X_val)
        val_f1 = f1_score(y_val, val_pred)
        base_metrics[name] = {"val_f1": float(val_f1)}
        fitted_estimators.append((name, model))
        joblib.dump(model, models_dir / f"{name}.joblib")

    ensemble = _build_ensemble(fitted_estimators)
    ensemble.fit(X_train, y_train)
    val_pred = ensemble.predict(X_val)
    val_f1 = f1_score(y_val, val_pred)
    logger.info("Ensemble validation F1: %.4f", val_f1)

    # Save full pipeline metadata
    joblib.dump(ensemble, models_dir / "ensemble.joblib")
    (models_dir / "feature_names.json").write_text(
        json.dumps(FEATURE_NAMES, indent=2), encoding="utf-8"
    )

    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "model_version": "1.0.0",
        "feature_count": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "base_learners": list(base_learners.keys()),
        "voting": "soft",
        "base_metrics": base_metrics,
        "ensemble_val_f1": float(val_f1),
        "random_state": RANDOM_STATE,
    }
    (models_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    logger.info("Models saved to %s", models_dir)
    return metadata


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train(tune=False)
