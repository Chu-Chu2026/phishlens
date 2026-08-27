"""App shell — sidebar + top header (Vite _app.tsx parity)."""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from streamlit_app.components.ui import LOGO_SVG
from streamlit_app.utils.nav import (
    CONFIDENCE_EVIDENCE,
    DASHBOARD,
    DATASET_ANALYTICS,
    EXPLAINABILITY,
    HOME_PAGE,
    MODEL_EVALUATION,
    RESEARCH,
    URL_ANALYSIS,
)

ROOT = Path(__file__).resolve().parents[2]

NAV_ITEMS: list[tuple[str, str, str, str]] = [
    ("dashboard", "Dashboard", DASHBOARD, "dashboard"),
    ("detect", "URL Detection", URL_ANALYSIS, "radar"),
    ("explain", "Explainability", EXPLAINABILITY, "auto_awesome"),
    ("performance", "Model Performance", MODEL_EVALUATION, "monitoring"),
    ("dataset", "Dataset Analytics", DATASET_ANALYTICS, "database"),
    ("research", "Research", RESEARCH, "menu_book"),
    ("confidence", "Confidence Evidence", CONFIDENCE_EVIDENCE, "psychology"),
]

NAV_LABELS = {nav_id: label for nav_id, label, _, _ in NAV_ITEMS}

_SCRIPT_TO_NAV: dict[str, str] = {
    "streamlit_app.py": "home",
    "app.py": "home",
    "1_Dashboard.py": "dashboard",
    "2_URL_Analysis.py": "detect",
    "3_Explainability.py": "explain",
    "4_Model_Evaluation.py": "performance",
    "5_Dataset_Analytics.py": "dataset",
    "6_Research.py": "research",
    "7_Confidence_Evidence.py": "confidence",
}


def detect_active_nav() -> str:
    """Infer active nav item from the running Streamlit script."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()
        if ctx and ctx.script_path:
            return _SCRIPT_TO_NAV.get(Path(ctx.script_path).name, "")
    except Exception:
        pass
    return ""


def inject_sidebar_shell_css() -> None:
    """Sidebar layout helpers — do not override Streamlit collapse width/transform."""
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
          display: flex !important;
          flex-direction: column !important;
          min-height: 100vh !important;
          padding: 0.5rem 0.65rem 0.75rem !important;
          gap: 0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]:has(#phish-sidebar-footer-anchor) {
          margin-top: auto !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
          background: transparent !important;
          border: none !important;
        }
        [data-testid="stSidebarCollapseButton"] {
          pointer-events: auto !important;
          flex-shrink: 0 !important;
        }
        [data-testid="stSidebarCollapseButton"] button {
          color: var(--muted-foreground) !important;
          pointer-events: auto !important;
        }
        [data-testid="stSidebarCollapseButton"] button:hover {
          color: var(--foreground) !important;
          background: oklch(0.24 0.03 264 / 0.55) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_brand() -> None:
    """Brand block — logo and home link."""
    b_icon, b_text = st.columns([0.22, 0.78], gap="small")
    with b_icon:
        st.markdown(
            f'<div class="phish-sidebar-logo">{LOGO_SVG}</div>',
            unsafe_allow_html=True,
        )
    with b_text:
        st.page_link(HOME_PAGE, label="PhishLens", help="Back to landing page")
        st.markdown('<span class="phish-sidebar-version">Research v1.0</span>', unsafe_allow_html=True)


def render_app_sidebar(active_nav: str | None = None) -> None:
    """Sidebar: brand, nav, and model status."""
    _ = active_nav  # reserved for future active-state styling
    model_online = (ROOT / "trained_models" / "ensemble.joblib").exists()

    inject_sidebar_shell_css()

    with st.sidebar:
        st.markdown('<div class="phish-sidebar-brand-wrap">', unsafe_allow_html=True)
        _render_brand()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="phish-sidebar-rule"></div>', unsafe_allow_html=True)
        st.markdown('<p class="phish-sidebar-section-label">Navigation</p>', unsafe_allow_html=True)

        st.markdown('<div class="phish-sidebar-nav-wrap">', unsafe_allow_html=True)
        for _nav_id, label, page, icon in NAV_ITEMS:
            st.page_link(
                page,
                label=label,
                icon=f":material/{icon}:",
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div id="phish-sidebar-footer-anchor"></div>', unsafe_allow_html=True)

        status_cls = "phish-sidebar-status phish-sidebar-status--online" if model_online else "phish-sidebar-status"
        status_text = "Model online" if model_online else "Model not trained"
        dot_cls = "phish-status-dot" if model_online else "phish-status-dot phish-status-dot--off"
        st.markdown(
            f'<div class="{status_cls}"><span class="{dot_cls}"></span>'
            f'<span class="phish-status-label">{html.escape(status_text)}</span></div>',
            unsafe_allow_html=True,
        )


def render_app_header(page_title: str, active_nav: str = "") -> None:
    """Sticky top bar — breadcrumb and model status."""
    model_online = (ROOT / "trained_models" / "ensemble.joblib").exists()
    crumb = NAV_LABELS.get(active_nav, page_title)
    dot_cls = "phish-header-dot--on" if model_online else "phish-header-dot--off"
    status_label = "Model online" if model_online else "Train model"

    left, right = st.columns([3, 1], gap="medium")
    with left:
        st.markdown(
            f"""
            <div class="phish-app-header-crumb">
              <span class="phish-crumb-root">PhishLens</span>
              <span class="phish-crumb-sep">/</span>
              <span class="phish-crumb-leaf">{html.escape(crumb)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div class="phish-header-status">
              <span class="phish-header-dot {dot_cls}"></span>
              <span>{html.escape(status_label)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="phish-app-header-rule"></div>', unsafe_allow_html=True)
