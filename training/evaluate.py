"""Offline model evaluation and artifact generation."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    auc,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from streamlit_app.utils.feature_extraction import extract_features_dataframe
from training.config import EVAL_DIR, ENSEMBLE_MODELS, MODELS_DIR, PLOTS_DIR, PROCESSED_DIR, RANDOM_STATE

logger = logging.getLogger(__name__)

# Plot style aligned with PhishLens dark theme
plt.style.use("dark_background")
COLORS = {
    "primary": "#6b9fff",
    "accent": "#5ec4d4",
    "danger": "#e85d5d",
    "success": "#5ec995",
}


def _load_test_data() -> tuple[pd.DataFrame, np.ndarray]:
    """Load test split features and labels."""
    df = pd.read_csv(PROCESSED_DIR / "test.csv")
    X = extract_features_dataframe(df["url"].tolist())
    y = df["label"].values
    return X, y


def _measure_latency(model, X: pd.DataFrame, n_samples: int = 100) -> dict:
    """Measure inference latency on a sample."""
    sample = X.head(n_samples)
    times: list[float] = []
    for i in range(len(sample)):
        row = sample.iloc[[i]]
        start = time.perf_counter()
        model.predict_proba(row)
        times.append((time.perf_counter() - start) * 1000)
    times_arr = np.array(times)
    return {
        "mean_ms": float(np.mean(times_arr)),
        "p50_ms": float(np.percentile(times_arr, 50)),
        "p95_ms": float(np.percentile(times_arr, 95)),
        "n_samples": n_samples,
    }


def _plot_confusion_matrix(y_true, y_pred, output_path: Path) -> None:
    """Save confusion matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Legitimate", "Phishing"],
        yticklabels=["Legitimate", "Phishing"],
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix — Test Set")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_roc(y_true, y_prob, output_path: Path) -> float:
    """Save ROC curve and return AUC."""
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color=COLORS["primary"], lw=2, label=f"AUC = {roc_auc:.4f}")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return float(roc_auc)


def _plot_pr(y_true, y_prob, output_path: Path) -> float:
    """Save precision-recall curve and return average precision."""
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    ap = float(average_precision_score(y_true, y_prob))
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall, precision, color=COLORS["accent"], lw=2, label=f"AP = {ap:.4f}")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision–Recall Curve")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ap


def _plot_model_comparison(comparison: list[dict], output_path: Path) -> None:
    """Save bar chart comparing model metrics."""
    df = pd.DataFrame(comparison)
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(df))
    width = 0.35
    ax.bar(x - width / 2, df["accuracy"], width, label="Accuracy", color=COLORS["primary"])
    ax.bar(x + width / 2, df["f1"], width, label="F1", color=COLORS["accent"])
    ax.set_xticks(x)
    ax.set_xticklabels(df["model"], rotation=15, ha="right")
    ax.set_ylim(0.5, 1.0)
    ax.set_title("Model Comparison — Test Set")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def evaluate(output_dir: Path | None = None) -> dict:
    """
    Evaluate ensemble and base learners on held-out test set.

    Returns:
        Dictionary of evaluation metrics and artifact paths.
    """
    output_dir = output_dir or EVAL_DIR
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    X_test, y_test = _load_test_data()
    ensemble = joblib.load(MODELS_DIR / "ensemble.joblib")

    y_pred = ensemble.predict(X_test)
    y_prob = ensemble.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "auc": float(roc_auc_score(y_test, y_prob)),
        "test_size": int(len(y_test)),
        "random_state": RANDOM_STATE,
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(
            y_test, y_pred, target_names=["Legitimate", "Phishing"], output_dict=True
        ),
    }

    latency = _measure_latency(ensemble, X_test)
    metrics["latency"] = latency

    # Base learner comparison
    comparison: list[dict] = []
    for name in ENSEMBLE_MODELS:
        model_path = MODELS_DIR / f"{name}.joblib"
        if model_path.exists():
            model = joblib.load(model_path)
            bp = model.predict(X_test)
            comparison.append({
                "model": name.replace("_", " ").title(),
                "accuracy": float(accuracy_score(y_test, bp)),
                "f1": float(f1_score(y_test, bp)),
            })
    comparison.append({
        "model": "Ensemble",
        "accuracy": metrics["accuracy"],
        "f1": metrics["f1"],
    })
    metrics["model_comparison"] = comparison

    # Generate plots
    _plot_confusion_matrix(y_test, y_pred, plots_dir / "confusion_matrix.png")
    metrics["auc_plot"] = _plot_roc(y_test, y_prob, plots_dir / "roc_curve.png")
    metrics["average_precision"] = _plot_pr(y_test, y_prob, plots_dir / "pr_curve.png")
    _plot_model_comparison(comparison, plots_dir / "model_comparison.png")

    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    logger.info("Evaluation metrics saved to %s", metrics_path)
    logger.info(
        "Test — Acc: %.4f, F1: %.4f, AUC: %.4f",
        metrics["accuracy"],
        metrics["f1"],
        metrics["auc"],
    )
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    evaluate()
