"""Explainability — SHAP visualisations and narratives."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from streamlit_app.components.analysis import ensure_fresh_explanation, get_explanation_field
from streamlit_app.components.ui import (
    glass_panel,
    init_page,
    narrative_box,
    page_header,
    section_title,
    shap_feature_bars,
    stat_chip,
    section_spacer,
)
from streamlit_app.services.explainer import (
    explain_url,
    load_global_importance,
    plot_force_bar,
    plot_waterfall,
)
from streamlit_app.services.model_loader import get_shap_plot_path

init_page("Explainability · PhishLens", "✨", active_nav="explain")

page_header(
    "Why PhishLens decided this",
    "Plain-English reasons first, with charts underneath for deeper inspection.",
    badge="Explainable AI · SHAP",
    accent=True,
)

ensure_fresh_explanation()
explanation = st.session_state.get("last_explanation")
url = st.session_state.get("last_url")

if explanation:
    final = explanation.base_value + explanation.shap_values.sum()
    pos_sum = sum(d["shap"] for d in explanation.top_positive)
    neg_sum = sum(abs(d["shap"]) for d in explanation.top_negative)
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        stat_chip("Base value", f"{explanation.base_value:.2f}", "E[f(x)]")
    with c2:
        stat_chip(
            "Final score",
            f"{final:.2f}",
            "phishing probability",
            "danger" if final > 0.6 else "neutral",
        )
    with c3:
        stat_chip("Positive push", f"+{pos_sum:.2f}", f"{len(explanation.top_positive)} features", "danger")
    with c4:
        stat_chip("Negative pull", f"−{neg_sum:.2f}", f"{len(explanation.top_negative)} features", "safe")
        section_spacer()
elif url:
    st.info("SHAP values are loading — analyze the URL again if this persists.")
else:
    st.info("Analyze a URL on **URL Analysis** or the landing page to see local SHAP attributions.")

tab_summary, tab_waterfall, tab_importance, tab_force, tab_local = st.tabs(
    ["Summary", "Waterfall", "Importance", "Force", "Plain-English explanation"]
)

with tab_summary:
    with glass_panel():
        section_title("SHAP Summary — bee-swarm", "Global feature impact across the test set")
        summary_path = get_shap_plot_path("summary_plot.png")
        if summary_path.exists():
            st.image(str(summary_path), width="stretch")
        else:
            st.warning("Run `python scripts/run_pipeline.py` to generate global SHAP plots.")

with tab_waterfall:
    with glass_panel():
        if not url:
            st.info("Analyze a URL on **URL Analysis** to see a local waterfall plot.")
        elif explanation is None:
            try:
                explanation = explain_url(url)
                st.session_state.last_explanation = explanation
            except Exception as exc:
                st.error(str(exc))
                explanation = None
        if explanation:
            try:
                fig = plot_waterfall(explanation)
                st.pyplot(fig)
                plt.close(fig)
            except Exception:
                st.warning("Waterfall unavailable — showing force-style chart.")
                fig = plot_force_bar(explanation)
                st.pyplot(fig)
                plt.close(fig)

with tab_importance:
    with glass_panel():
        section_title("Global feature importance", "Mean |SHAP| ranking across test set")
        bar_path = get_shap_plot_path("importance_bar.png")
        if bar_path.exists():
            st.image(str(bar_path), width="stretch")
        importance = load_global_importance()
        if importance:
            st.dataframe(pd.DataFrame(importance).head(15), width="stretch", hide_index=True)
        else:
            st.info("Run the training pipeline to generate SHAP artifacts.")

with tab_force:
    with glass_panel():
        if not url or explanation is None:
            st.info("Analyze a URL first to view the force plot for that prediction.")
        else:
            section_title("Force plot", "Push and pull forces on this prediction")
            fig = plot_force_bar(explanation)
            st.pyplot(fig)
            plt.close(fig)

with tab_local:
    if not url:
        with glass_panel():
            st.info("Analyze a URL on **URL Analysis** first, or enter one below.")
            demo_url = st.text_input("URL", placeholder="https://...", label_visibility="collapsed")
            if st.button("Explain this URL", type="primary") and demo_url:
                try:
                    st.session_state.last_url = demo_url
                    st.session_state.last_explanation = explain_url(demo_url)
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    else:
        if explanation is None:
            try:
                explanation = explain_url(url)
                st.session_state.last_explanation = explanation
            except Exception as exc:
                st.error(str(exc))
                explanation = None

        if explanation:
            with glass_panel(strong=True):
                st.markdown(f"**URL:** `{url}`")
                narrative_box(get_explanation_field(explanation, "narrative", "") or "")
                advice = get_explanation_field(explanation, "advice", "") or ""
                if advice:
                    st.info(advice)

            col_push, col_pull = st.columns(2, gap="medium")
            with col_push:
                with glass_panel():
                    section_title("Warning signs → phishing")
                    risk_reasons = get_explanation_field(explanation, "plain_reasons_risk", []) or []
                    for reason in risk_reasons[:6]:
                        st.markdown(f"- {reason}")
                    shap_feature_bars(
                        get_explanation_field(explanation, "top_positive", []) or [],
                        max_items=6,
                    )
            with col_pull:
                with glass_panel():
                    section_title("Reassuring signs → legitimate")
                    safe_reasons = get_explanation_field(explanation, "plain_reasons_safe", []) or []
                    for reason in safe_reasons[:6]:
                        st.markdown(f"- {reason}")
                    shap_feature_bars(
                        list(get_explanation_field(explanation, "top_negative", []) or []),
                        max_items=6,
                    )

st.caption(
    "Explanations are written for everyday users first. "
    "Technical SHAP values still power the charts, using TreeExplainer on the Random Forest "
    "model inside the soft-voting ensemble as a clear, practical proxy."
)
