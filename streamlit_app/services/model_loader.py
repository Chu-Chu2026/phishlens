"""Model loading and caching for Streamlit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import streamlit as st

from training.config import EVAL_DIR, MODELS_DIR


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@st.cache_resource(show_spinner="Loading ensemble model…")
def load_ensemble():
    """Load the trained voting ensemble classifier."""
    path = _project_root() / "trained_models" / "ensemble.joblib"
    if not path.exists():
        raise FileNotFoundError(
            "Trained model not found. Run: python -m training.train"
        )
    return joblib.load(path)


@st.cache_resource(show_spinner="Loading model metadata…")
def load_metadata() -> dict[str, Any]:
    """Load model training metadata."""
    path = _project_root() / "trained_models" / "metadata.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


@st.cache_resource(show_spinner="Loading evaluation metrics…")
def load_metrics() -> dict[str, Any]:
    """Load offline evaluation metrics."""
    path = _project_root() / "evaluation" / "metrics.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


@st.cache_resource(show_spinner="Loading dataset statistics…")
def load_dataset_stats() -> dict[str, Any]:
    """Load dataset analytics statistics."""
    path = _project_root() / "evaluation" / "dataset_stats.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


@st.cache_resource(show_spinner="Initialising SHAP explainer…")
def load_shap_explainer():
    """Load SHAP TreeExplainer backed by ensemble tree model."""
    import shap

    ensemble = load_ensemble()
    if hasattr(ensemble, "named_estimators_") and "random_forest" in ensemble.named_estimators_:
        tree_model = ensemble.named_estimators_["random_forest"]
    else:
        tree_model = ensemble
    return shap.TreeExplainer(tree_model)


def get_plot_path(name: str) -> Path:
    """Return path to a pre-generated evaluation plot."""
    return _project_root() / "evaluation" / "plots" / name


def get_shap_plot_path(name: str) -> Path:
    """Return path to a pre-generated SHAP plot."""
    return _project_root() / "evaluation" / "shap" / name
