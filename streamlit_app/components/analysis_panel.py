"""Render URL analysis results panel (shared by Dashboard and URL Analysis)."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from streamlit_app.components.ui import (
    anatomy_table,
    confidence_ring,
    glass_panel,
    narrative_box,
    risk_badge,
    section_spacer,
    section_title,
    shap_feature_bars,
    verdict_badge,
)
from streamlit_app.components.analysis import get_explanation_field
from streamlit_app.services.explainer import ExplanationResult
from streamlit_app.services.predictor import PredictionResult
from streamlit_app.utils.nav import CONFIDENCE_EVIDENCE, EXPLAINABILITY


def render_why_decision(pred: PredictionResult, expl: ExplanationResult | None) -> None:
    """
    Always show a plain-English section explaining why the URL was
    classified as phishing or legitimate.
    """
    verdict = pred.prediction
    is_phish = verdict == "Phishing"
    section_title(
        f"Why we said {verdict}",
        "Always shown after analysis — written for non-technical users",
    )

    with glass_panel(strong=True):
        if is_phish:
            st.markdown(
                f"**Verdict:** PhishLens flagged this link as **phishing** "
                f"with **{pred.confidence:.0%}** confidence "
                f"(phishing probability **{pred.phishing_probability:.0%}**, "
                f"risk level **{pred.risk_level}**)."
            )
        else:
            st.markdown(
                f"**Verdict:** PhishLens classified this link as **legitimate** "
                f"with **{pred.confidence:.0%}** confidence "
                f"(legitimate probability **{pred.legitimate_probability:.0%}**, "
                f"risk level **{pred.risk_level}**)."
            )

        risk_reasons = get_explanation_field(expl, "plain_reasons_risk", []) or []
        safe_reasons = get_explanation_field(expl, "plain_reasons_safe", []) or []
        advice = get_explanation_field(expl, "advice", "") or ""
        narrative = get_explanation_field(expl, "narrative", "") or ""

        if narrative:
            narrative_box(narrative)
        else:
            st.warning(
                "A detailed explanation is not available yet. "
                "Re-run the analysis, or run `python scripts/run_pipeline.py` "
                "if the model/SHAP artifacts are missing."
            )

        left, right = st.columns(2, gap="medium")
        with left:
            st.markdown(
                "#### Why it looks like phishing" if is_phish else "#### Mild warning signs"
            )
            if risk_reasons:
                for reason in risk_reasons[:5]:
                    st.markdown(f"- {reason}")
            elif is_phish:
                st.caption("No detailed warning reasons were produced for this URL.")
            else:
                st.caption("No strong warning signs dominated this decision.")

        with right:
            st.markdown(
                "#### Why it looks legitimate" if not is_phish else "#### What looked safer"
            )
            if safe_reasons:
                for reason in safe_reasons[:5]:
                    st.markdown(f"- {reason}")
            elif not is_phish:
                st.caption("No detailed reassuring reasons were produced for this URL.")
            else:
                st.caption(
                    "Safer signals were present but not strong enough to change the verdict."
                )

        if advice:
            st.info(advice)

        top_positive = get_explanation_field(expl, "top_positive", []) or []
        top_negative = get_explanation_field(expl, "top_negative", []) or []
        if top_positive or top_negative:
            section_title("Top reasons ranked by impact", "Plain-English decision drivers")
            shap_feature_bars(
                list(top_positive) + list(top_negative),
                max_items=8,
            )

    st.page_link(EXPLAINABILITY, label="See charts and deeper SHAP detail →")
    section_spacer()


def render_verdict_card(pred: PredictionResult) -> None:
    """Compact verdict header for the latest analysis."""
    is_phish = pred.prediction == "Phishing"
    pct = round(pred.confidence * 100)

    with glass_panel(strong=True):
        c1, c2, c3 = st.columns([1.2, 1, 1], gap="medium")
        with c1:
            verdict_badge(pred.prediction, pred.confidence)
            risk_badge(pred.risk_level)
            st.markdown(
                f'<p class="analysis-url">{html.escape(pred.url)}</p>',
                unsafe_allow_html=True,
            )
            st.caption("Ensemble soft-vote · Model v1.0")
        with c2:
            confidence_ring(pct, is_phish)
        with c3:
            st.markdown(
                f"""
                <div class="inline-metrics">
                  <div><span class="inline-metric-label">Phishing</span>
                  <span class="inline-metric-value">{pred.phishing_probability:.1%}</span></div>
                  <div><span class="inline-metric-label">Legitimate</span>
                  <span class="inline-metric-value">{pred.legitimate_probability:.1%}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_analysis_details(
    pred: PredictionResult,
    expl: ExplanationResult | None,
) -> None:
    """URL anatomy, model votes, and ranked drivers."""
    col_a, col_b, col_c = st.columns(3, gap="medium")

    with col_a:
        with glass_panel():
            section_title("URL at a glance", "What we can see in the link")
            host = pred.host_details
            anatomy_table([
                ("Website name", host.get("hostname", "")),
                ("Connection", host.get("scheme", "").upper()),
                ("Ending (TLD)", f".{host.get('tld', '')}"),
                ("Link length", f"{host.get('length', 0)} characters"),
                ("Extra prefixes", str(host.get("subdomains", 0))),
                ("Folder depth", str(host.get("path_depth", 0))),
                ("Extra parameters", str(host.get("query_params", 0))),
                ("Hyphens", str(host.get("hyphens", 0))),
                ("Digits", str(host.get("digits", 0))),
                ("Raw IP address?", "Yes" if host.get("has_ip") else "No"),
            ])

    with col_b:
        with glass_panel():
            section_title("Model agreement", "How each model voted")
            if pred.model_votes:
                votes_df = pd.DataFrame(pred.model_votes)
                st.dataframe(
                    votes_df[["model", "prediction", "probability"]].rename(
                        columns={"probability": "confidence"}
                    ),
                    width="stretch",
                    hide_index=True,
                )
            st.caption("Final answer combines Logistic Regression, Random Forest, and SVM.")

    with col_c:
        with glass_panel():
            section_title("Biggest decision drivers", "Plain-English impact ranking")
            if expl:
                shap_feature_bars(
                    list(expl.top_positive) + list(expl.top_negative),
                    max_items=8,
                )
            else:
                st.caption("Run an analysis to see ranked drivers.")

    st.page_link(EXPLAINABILITY, label="View full charts & deeper explanation →")
    st.page_link(
        CONFIDENCE_EVIDENCE,
        label="Record whether this explanation increased your confidence →",
    )


def render_analysis_results(
    pred: PredictionResult,
    expl: ExplanationResult | None,
    *,
    include_why: bool = True,
) -> None:
    """Full analysis result panel: verdict → why → details."""
    render_verdict_card(pred)
    if include_why:
        render_why_decision(pred, expl)
    render_analysis_details(pred, expl)
