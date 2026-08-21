"""Integration tests for prediction pipeline and plain-English explanations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODEL_PATH = ROOT / "trained_models" / "ensemble.joblib"


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model not trained")
def test_predict_phishing_url():
    from streamlit_app.services.predictor import predict_url

    result, validation = predict_url("https://secure-login-microsft.com/verify")
    assert validation.is_valid
    assert result is not None
    assert result.prediction == "Phishing"
    assert result.phishing_probability >= 0.5
    assert result.risk_level in {"Low", "Medium", "High", "Critical"}
    assert result.model_votes
    model_names = {v["model"] for v in result.model_votes}
    assert "Logistic Regression" in model_names
    assert "Random Forest" in model_names
    assert any("Svm" in name or "SVM" in name.upper() for name in model_names)


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model not trained")
def test_predict_legitimate_url():
    from streamlit_app.services.predictor import predict_url

    result, validation = predict_url("https://github.com")
    assert validation.is_valid
    assert result is not None
    assert result.prediction == "Legitimate"
    assert result.legitimate_probability >= 0.5


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model not trained")
def test_shap_explanation():
    from streamlit_app.services.explainer import explain_url

    explanation = explain_url("https://secure-login-microsft.com/verify")
    assert len(explanation.shap_values) > 0
    assert explanation.narrative
    assert "plain english" in explanation.narrative.lower()
    assert explanation.advice
    assert explanation.plain_reasons_risk or explanation.plain_reasons_safe
    assert all("label" in item for item in explanation.top_positive[:3])
    # Narrative should speak in everyday language, not raw snake_case feature dumps
    assert "suspicious_keyword_count" not in explanation.narrative


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model not trained")
def test_legitimate_explanation_is_human_readable():
    from streamlit_app.services.explainer import explain_url

    explanation = explain_url("https://github.com")
    assert "plain english" in explanation.narrative.lower()
    assert "What you should do" in explanation.narrative
    assert explanation.advice


def test_plain_english_labels_present():
    from streamlit_app.services.explainer import FEATURE_GUIDE, plain_label

    assert plain_label("has_ip_host") == "Uses a raw IP address instead of a name"
    assert "login" in FEATURE_GUIDE["suspicious_keyword_count"]["risk"].lower()
    assert len(FEATURE_GUIDE) >= 30


def test_confidence_storage_and_uplift(tmp_path):
    """Confidence evidence records can be saved and summarised for uplift."""
    rows = [
        {"analyst_id": "P01", "confidence_before": 2, "confidence_after": 4, "delta": 2},
        {"analyst_id": "P02", "confidence_before": 3, "confidence_after": 5, "delta": 2},
    ]
    path = tmp_path / "user_confidence.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    before = sum(r["confidence_before"] for r in loaded) / len(loaded)
    after = sum(r["confidence_after"] for r in loaded) / len(loaded)
    assert before == 2.5
    assert after == 4.5
    assert after - before == 2.0
