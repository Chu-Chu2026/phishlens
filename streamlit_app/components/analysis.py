"""Shared URL analysis session helpers and result rendering."""

from __future__ import annotations

import streamlit as st

from streamlit_app.services.explainer import explain_url
from streamlit_app.services.predictor import predict_url


def ensure_analysis_state() -> None:
    """Initialize session state keys used across pages."""
    defaults = {
        "last_url": None,
        "last_prediction": None,
        "last_explanation": None,
        "pending_url": None,
        "auto_analyze": False,
        "_phish_loader_done": False,
        "analysis_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def run_analysis(url: str) -> tuple[bool, str | None]:
    """
    Run prediction + SHAP for a URL and store in session state.

    Returns:
        (success, error_message)
    """
    ensure_analysis_state()
    try:
        result, validation = predict_url(url)
        if not validation.is_valid:
            return False, validation.error or "Invalid URL"
        if result is None:
            return False, "Analysis returned no result"
        st.session_state.last_url = result.url
        st.session_state.last_prediction = result
        st.session_state.last_explanation = explain_url(result.url)
        history = list(st.session_state.get("analysis_history", []))
        history.insert(
            0,
            {
                "url": result.url,
                "prediction": result.prediction,
                "confidence": result.confidence,
                "risk": result.risk_level,
            },
        )
        st.session_state.analysis_history = history[:10]
        st.session_state.pending_url = None
        st.session_state.auto_analyze = False
        return True, None
    except FileNotFoundError:
        return False, "Trained model not found. Run: python scripts/run_pipeline.py"
    except Exception as exc:
        return False, str(exc)


def clear_analysis() -> None:
    """Clear stored analysis from session."""
    ensure_analysis_state()
    st.session_state.last_url = None
    st.session_state.last_prediction = None
    st.session_state.last_explanation = None
    st.session_state.pending_url = None
    st.session_state.auto_analyze = False


def ensure_fresh_explanation() -> None:
    """
    Rebuild last_explanation if it is stale (from an older app version)
    or missing plain-English fields like advice / plain_reasons_*.
    """
    ensure_analysis_state()
    expl = st.session_state.get("last_explanation")
    url = st.session_state.get("last_url")
    if expl is None or not url:
        return
    required = ("advice", "plain_reasons_risk", "plain_reasons_safe", "narrative")
    if all(hasattr(expl, name) for name in required):
        return
    try:
        st.session_state.last_explanation = explain_url(url)
    except Exception:
        # Keep the old object if refresh fails; UI will degrade gracefully.
        pass


def get_explanation_field(expl: object | None, name: str, default=None):
    """Safely read explanation fields across app versions."""
    if expl is None:
        return default
    return getattr(expl, name, default)


def has_pending_analysis() -> bool:
    """Return True when a queued URL should be analyzed on page load."""
    ensure_analysis_state()
    return bool(st.session_state.auto_analyze and st.session_state.pending_url)


def queue_analysis(url: str) -> None:
    """Queue a URL for auto-analysis on the next dashboard load."""
    ensure_analysis_state()
    st.session_state.pending_url = url.strip()
    st.session_state.auto_analyze = True


def process_pending_analysis() -> str | None:
    """
    If a URL is queued, run analysis.

    Returns:
        Error message if failed, else None.
    """
    ensure_analysis_state()
    if not st.session_state.auto_analyze or not st.session_state.pending_url:
        return None
    ok, err = run_analysis(st.session_state.pending_url)
    return err if not ok else None
