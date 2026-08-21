"""Full-screen loading splash for PhishLens."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui import LOGO_SVG


def inject_loading_screen() -> None:
    """Branded splash — CSS animation, once per Streamlit session."""
    if st.session_state.get("_phish_loader_done"):
        return
    st.session_state._phish_loader_done = True

    st.markdown(
        f"""
        <div id="phish-loader" aria-live="polite" aria-busy="true"
          style="position:fixed;inset:0;z-index:999999;display:grid;place-items:center;">
          <div class="phish-loader-card">
            <div class="phish-loader-logo">{LOGO_SVG.strip()}</div>
            <div class="phish-loader-title">PhishLens</div>
            <div class="phish-loader-sub">Explainable phishing detection</div>
            <div class="phish-loader-ring" role="status"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
