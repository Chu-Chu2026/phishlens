"""Prediction service for URL phishing detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from streamlit_app.services.model_loader import load_ensemble, load_metadata
from streamlit_app.utils.feature_extraction import (
    FEATURE_NAMES,
    extract_features_dataframe,
    get_parsed_url_details,
)
from streamlit_app.utils.url_validation import URLValidationResult, validate_url
from training.config import LABEL_NAMES, RISK_THRESHOLDS


@dataclass
class PredictionResult:
    """Full prediction output for a single URL."""

    url: str
    prediction: str
    label: int
    confidence: float
    phishing_probability: float
    legitimate_probability: float
    risk_level: str
    features: pd.DataFrame
    model_votes: list[dict[str, Any]] = field(default_factory=list)
    host_details: dict[str, Any] = field(default_factory=dict)


def _risk_level(probability: float) -> str:
    """Map phishing probability to risk level."""
    for level, (low, high) in RISK_THRESHOLDS.items():
        if low <= probability < high:
            return level
    return "Critical"


def predict_url(raw_url: str) -> tuple[PredictionResult | None, URLValidationResult]:
    """
    Validate URL, extract features, and run ensemble prediction.

    Returns:
        Tuple of (PredictionResult or None, URLValidationResult).
    """
    validation = validate_url(raw_url)
    if not validation.is_valid:
        return None, validation

    url = validation.normalized_url
    features = extract_features_dataframe([url])
    ensemble = load_ensemble()

    proba = ensemble.predict_proba(features)[0]
    label = int(np.argmax(proba))
    confidence = float(proba[label])
    phishing_prob = float(proba[1])

    # Per-model votes from VotingClassifier
    votes: list[dict[str, Any]] = []
    if hasattr(ensemble, "named_estimators_"):
        for name, estimator in ensemble.named_estimators_.items():
            est_proba = estimator.predict_proba(features)[0]
            est_label = int(np.argmax(est_proba))
            votes.append({
                "model": name.replace("_", " ").title(),
                "prediction": LABEL_NAMES[est_label],
                "probability": float(est_proba[est_label]),
                "phishing_probability": float(est_proba[1]),
            })

    result = PredictionResult(
        url=url,
        prediction=LABEL_NAMES[label],
        label=label,
        confidence=confidence,
        phishing_probability=phishing_prob,
        legitimate_probability=float(proba[0]),
        risk_level=_risk_level(phishing_prob),
        features=features,
        model_votes=votes,
        host_details=get_parsed_url_details(url),
    )
    return result, validation
