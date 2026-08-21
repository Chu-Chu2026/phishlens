"""URL Analysis — classify URLs with ensemble model."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from streamlit_app.components.analysis import (
    clear_analysis,
    ensure_analysis_state,
    ensure_fresh_explanation,
    has_pending_analysis,
    process_pending_analysis,
    run_analysis,
)
from streamlit_app.components.analysis_panel import render_analysis_results
from streamlit_app.components.ui import glass_panel, init_page, page_header

ensure_analysis_state()
init_page("URL Analysis · PhishLens", "🔍", active_nav="detect")

page_header(
    "URL Detection",
    "Submit a URL to receive a classification, confidence score, risk level, and SHAP-backed explanation.",
    badge="Workflow",
    accent=True,
)

if has_pending_analysis():
    with st.spinner("Running analysis…"):
        pending_err = process_pending_analysis()
else:
    pending_err = process_pending_analysis()

if pending_err:
    st.error(pending_err)
    st.code("python scripts/run_pipeline.py", language="bash")

with glass_panel(strong=True):
    url_input = st.text_input("URL", placeholder="https://example.com/login", label_visibility="collapsed")
    btn_col1, btn_col2 = st.columns(2, gap="medium")
    with btn_col1:
        analyze = st.button("🔍 Analyze", type="primary", width="stretch")
    with btn_col2:
        clear = st.button("Clear", width="stretch")
    st.caption(
        "Try `https://secure-login-microsft.com/verify` (phishing) or "
        "`https://github.com` (benign)."
    )

if clear:
    clear_analysis()
    st.rerun()

if analyze:
    if not url_input or not url_input.strip():
        st.warning("Enter a URL to analyze.")
    else:
        with st.spinner("Computing SHAP explanation…"):
            ok, err = run_analysis(url_input)
        if ok:
            st.toast(f"Analysis complete — {st.session_state.last_prediction.prediction}", icon="✅")
            st.rerun()
        elif err:
            if "Trained model not found" in err:
                st.error(err)
                st.code("python scripts/run_pipeline.py", language="bash")
            else:
                st.error(err)

pred = st.session_state.last_prediction
if pred:
    ensure_fresh_explanation()
    render_analysis_results(pred, st.session_state.last_explanation)
