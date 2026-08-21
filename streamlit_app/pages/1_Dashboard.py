"""Dashboard — research overview, model metrics, and URL analysis results."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from streamlit_app.components.analysis import (
    ensure_analysis_state,
    ensure_fresh_explanation,
    has_pending_analysis,
    process_pending_analysis,
)
from streamlit_app.components.analysis_panel import (
    render_analysis_details,
    render_verdict_card,
    render_why_decision,
)
from streamlit_app.components.ui import (
    glass_panel,
    hero_section,
    init_page,
    metrics_row,
    section_title,
)
from streamlit_app.services.model_loader import load_dataset_stats, load_metadata, load_metrics
from streamlit_app.utils.nav import (
    CONFIDENCE_EVIDENCE,
    DATASET_ANALYTICS,
    EXPLAINABILITY,
    MODEL_EVALUATION,
    RESEARCH,
    URL_ANALYSIS,
)

ensure_analysis_state()
init_page("Dashboard · PhishLens", "📊", active_nav="dashboard")

if has_pending_analysis():
    with st.spinner("Running analysis…"):
        analysis_err = process_pending_analysis()
else:
    analysis_err = process_pending_analysis()

if analysis_err:
    st.error(analysis_err)
    st.code("python scripts/run_pipeline.py", language="bash")

metrics = load_metrics()
meta = load_metadata()
stats = load_dataset_stats()

hero_section(
    "Explainable Ensemble ML for Phishing Detection",
    "Research overview, model metrics, and live URL analysis.",
    badge="Research prototype",
    show_ctas=True,
)

pred = st.session_state.last_prediction
ensure_fresh_explanation()
expl = st.session_state.last_explanation
if pred:
    section_title("Latest analysis", f"Results for `{pred.url}`")
    render_verdict_card(pred)
    # Always explain the classification immediately after Latest analysis
    render_why_decision(pred, expl)
    render_analysis_details(pred, expl)
    st.divider()
else:
    with glass_panel():
        section_title("Latest analysis", "No URL analysed yet")
        st.markdown(
            "Analyse a URL from the landing page or **URL Detection** to see the verdict "
            "and a plain-English explanation of why it was called phishing or legitimate."
        )
        st.page_link(URL_ANALYSIS, label="Analyse a URL →")

metrics_row([
    {"label": "Accuracy", "value": f"{metrics.get('accuracy', 0):.1%}" if metrics else "—", "icon_key": "accuracy"},
    {"label": "Precision", "value": f"{metrics.get('precision', 0):.1%}" if metrics else "—", "icon_key": "precision"},
    {"label": "Recall", "value": f"{metrics.get('recall', 0):.1%}" if metrics else "—", "icon_key": "recall"},
    {"label": "F1 Score", "value": f"{metrics.get('f1', 0):.3f}" if metrics else "—", "icon_key": "f1"},
    {"label": "Dataset", "value": f"{stats.get('total_urls', 0):,}" if stats else "—", "sub": "URLs", "icon_key": "dataset"},
    {"label": "Model", "value": meta.get("model_version", "—"), "sub": "ensemble", "icon_key": "model"},
])

left, right = st.columns([2, 1], gap="large")

with left:
    with glass_panel():
        section_title("Research objective")
        st.markdown(
            "Investigate whether an ensemble of **Logistic Regression**, **Random Forest**, "
            "and **Support Vector Machine (SVM)** — combined with SHAP explanations — can produce "
            "phishing detection that is both **accurate** and **interpretable** enough to "
            "be trusted by analysts."
        )
        if metrics and metrics.get("model_comparison"):
            section_title("Model comparison", "Test set performance across candidates")
            st.dataframe(
                pd.DataFrame(metrics["model_comparison"]),
                width="stretch",
                hide_index=True,
            )

with right:
    with glass_panel():
        section_title("Dataset summary")
        if stats:
            for label, key in [
                ("Dataset", "total_urls"),
                ("Features", "feature_count"),
                ("Phishing", "phishing_count"),
                ("Legitimate", "legitimate_count"),
            ]:
                val = stats.get(key, 0)
                fmt = f"{val:,}" if isinstance(val, int) and key != "feature_count" else str(val)
                st.markdown(f"- **{label}:** {fmt}")
        section_title("Quick navigation")
        st.page_link(URL_ANALYSIS, label="Analyze a URL →")
        st.page_link(EXPLAINABILITY, label="View SHAP explanations →")
        st.page_link(MODEL_EVALUATION, label="Model evaluation →")
        st.page_link(DATASET_ANALYTICS, label="Dataset analytics →")
        st.page_link(RESEARCH, label="Research documentation →")
        st.page_link(CONFIDENCE_EVIDENCE, label="Confidence evidence →")

history = st.session_state.get("analysis_history", [])
if history:
    with glass_panel():
        section_title("Recent analyses", "Session history (local prototype)")
        st.dataframe(
            pd.DataFrame(history),
            width="stretch",
            hide_index=True,
            column_config={
                "url": st.column_config.TextColumn("URL", width="large"),
                "prediction": "Verdict",
                "confidence": st.column_config.NumberColumn("Confidence", format="%.1%"),
                "risk": "Risk",
            },
        )

st.caption("All metrics computed on held-out test split — see evaluation/metrics.json.")
