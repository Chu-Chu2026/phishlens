"""Reusable Streamlit UI components — ported from src/components/phish/ui.tsx."""

from __future__ import annotations

import html
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]

# Shield-check logo SVG (matches Vite Lucide icon in gradient box)
LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
  fill="none" stroke="#0b1020" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
  <path d="m9 12 2 2 4-4"/>
</svg>
"""

METRIC_ICONS = {
    "accuracy": "🛡️",
    "precision": "📈",
    "recall": "📊",
    "f1": "📐",
    "dataset": "🗄️",
    "model": "🔀",
    "auc": "⚡",
    "latency": "⏱️",
    "test": "🧪",
    "urls": "🔗",
    "legitimate": "✅",
    "phishing": "⚠️",
    "features": "🧬",
}

def inject_custom_css() -> None:
    """Inject PhishLens theme CSS and Inter font."""
    from streamlit_app.components.loading import inject_loading_screen

    css_path = Path(__file__).resolve().parents[1] / "assets" / "custom.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    inject_loading_screen()


@contextmanager
def glass_panel(strong: bool = False) -> Iterator[None]:
    """Bordered container that picks up glass styling from custom.css."""
    _ = strong  # reserved for stronger variant via CSS later
    with st.container(border=True):
        yield


def plot_placeholder(title: str, hint: str = "Run the training pipeline to generate this plot.") -> None:
    """Empty-state panel for missing evaluation artifacts."""
    st.markdown(
        f"""
        <div class="plot-placeholder">
          <div class="plot-placeholder-title">{html.escape(title)}</div>
          <div class="plot-placeholder-hint">{html.escape(hint)}</div>
          <code>python scripts/run_pipeline.py</code>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_landing_css() -> None:
    """Hide sidebar on landing only — do not use initial_sidebar_state=collapsed (persists for session)."""
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
          display: none !important;
          visibility: hidden !important;
        }
        section.main .block-container {
          max-width: 80rem !important;
          padding-left: max(1rem, env(safe-area-inset-left)) !important;
          padding-right: max(1rem, env(safe-area-inset-right)) !important;
          padding-top: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_app_sidebar_css() -> None:
    """Deprecated — use sidebar.inject_sidebar_shell_css."""
    from streamlit_app.components.sidebar import inject_sidebar_shell_css

    inject_sidebar_shell_css()


def init_landing_page(title: str = "PhishLens", icon: str = "🛡️") -> None:
    """Landing page setup — full-width, no sidebar."""
    from streamlit_app.components.analysis import ensure_analysis_state

    ensure_analysis_state()
    # Keep sidebar expanded in Streamlit config (only applied once per session).
    # Hiding is done via CSS so dashboard pages still get a sidebar after navigation.
    st.set_page_config(page_title=title, page_icon=icon, layout="wide", initial_sidebar_state="expanded")
    inject_custom_css()
    inject_landing_css()


def init_page(
    title: str,
    icon: str = "🛡️",
    layout: str = "wide",
    active_nav: str | None = None,
) -> None:
    """Standard app page setup: config, CSS, sidebar, top header."""
    from streamlit_app.components.analysis import ensure_analysis_state
    from streamlit_app.components.sidebar import (
        detect_active_nav,
        render_app_header,
        render_app_sidebar,
    )

    ensure_analysis_state()
    nav = active_nav if active_nav is not None else detect_active_nav()

    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state="expanded",
    )
    inject_custom_css()
    render_app_sidebar(active_nav=nav)
    render_app_header(_page_title_from_config_sidebar(title), active_nav=nav)


def _page_title_from_config_sidebar(title: str) -> str:
    return title.split("·")[0].strip() if "·" in title else title


def render_sidebar() -> None:
    """Legacy alias — use render_app_sidebar from sidebar.py."""
    from streamlit_app.components.sidebar import render_app_sidebar

    render_app_sidebar()


def page_header(title: str, subtitle: str = "", badge: str = "", accent: bool = False) -> None:
    """Render page header with optional badge."""
    if badge:
        cls = "phish-badge phish-badge-accent" if accent else "phish-badge"
        st.markdown(f'<span class="{cls}">{html.escape(badge)}</span>', unsafe_allow_html=True)
    st.markdown(f"## {html.escape(title)}")
    if subtitle:
        st.markdown(
            f'<p class="section-subtitle" style="margin-bottom:1.5rem;">{html.escape(subtitle)}</p>',
            unsafe_allow_html=True,
        )


def hero_section(
    title: str,
    description: str,
    badge: str = "Research prototype",
    show_ctas: bool = False,
) -> None:
    """Glass hero banner like dashboard in Vite UI."""
    st.markdown(
        f"""
        <div class="glass-strong hero-section hero-bg">
          <span class="phish-badge">✨ {html.escape(badge)}</span>
          <h1 class="hero-title">{html.escape(title)}</h1>
          <p class="hero-desc">{html.escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if show_ctas:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            if st.button("🔍 Analyze URL", type="primary", width="stretch", key="hero_analyze"):
                st.switch_page("pages/2_URL_Analysis.py")
        with c2:
            if st.button("✨ View explanations", width="stretch", key="hero_explain"):
                st.switch_page("pages/3_Explainability.py")


def section_title(title: str, subtitle: str = "") -> None:
    """SectionTitle component from Vite."""
    sub = f'<p class="section-subtitle">{html.escape(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f'<div style="margin-bottom:1rem;"><h3 class="section-title">{html.escape(title)}</h3>{sub}</div>',
        unsafe_allow_html=True,
    )


def metric_card(
    label: str,
    value: str,
    delta: str = "",
    sub: str = "",
    icon_key: str = "",
) -> None:
    """MetricCard with icon — mirrors src/components/phish/ui.tsx."""
    icon = METRIC_ICONS.get(icon_key, "📌")
    delta_html = f'<div class="metric-delta">↗ {html.escape(delta)}</div>' if delta else ""
    sub_html = f'<span class="metric-sub">{html.escape(sub)}</span>' if sub else ""
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-card-header">
            <span class="metric-label">{html.escape(label)}</span>
            <span class="metric-icon">{icon}</span>
          </div>
          <div class="metric-value">{html.escape(value)}{sub_html}</div>
          {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metrics_row(cards: list[dict[str, str]]) -> None:
    """Responsive metrics grid."""
    items = []
    for c in cards:
        icon = METRIC_ICONS.get(c.get("icon_key", ""), "📌")
        sub = f'<span class="metric-sub">{html.escape(c.get("sub", ""))}</span>' if c.get("sub") else ""
        delta = f'<div class="metric-delta">↗ {html.escape(c["delta"])}</div>' if c.get("delta") else ""
        items.append(
            f"""<div class="metric-card">
              <div class="metric-card-header">
                <span class="metric-label">{html.escape(c["label"])}</span>
                <span class="metric-icon">{icon}</span>
              </div>
              <div class="metric-value">{html.escape(c["value"])}{sub}</div>{delta}
            </div>"""
        )
    st.markdown(f'<div class="phish-metrics-grid">{"".join(items)}</div>', unsafe_allow_html=True)


def glass_panel_start(strong: bool = False) -> None:
    """Open a glass panel (use markdown wrapper)."""
    cls = "glass-strong panel-card" if strong else "glass panel-card"
    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)


def glass_panel_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def stat_chip(label: str, value: str, hint: str = "", tone: str = "neutral") -> None:
    """Stat chip from explain page."""
    colors = {
        "neutral": ("var(--primary)", "oklch(0.72 0.16 252 / 0.2)"),
        "danger": ("var(--destructive)", "oklch(0.65 0.22 25 / 0.2)"),
        "safe": ("var(--success)", "oklch(0.74 0.14 158 / 0.2)"),
    }
    dot_color, ring = colors.get(tone, colors["neutral"])
    st.markdown(
        f"""
        <div class="stat-chip" style="box-shadow: inset 0 0 0 1px {ring};">
          <div class="stat-chip-label">
            <span class="stat-dot" style="background:{dot_color};"></span>
            {html.escape(label)}
          </div>
          <div class="stat-chip-value">{html.escape(value)}</div>
          <div class="stat-chip-hint">{html.escape(hint)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def verdict_badge(prediction: str, confidence: float) -> None:
    """Prediction verdict hero card."""
    css_class = "verdict-phishing" if prediction == "Phishing" else "verdict-legit"
    st.markdown(
        f"""
        <div class="verdict-box {css_class}">
          <div class="verdict-label">Prediction</div>
          <div class="verdict-value">{html.escape(prediction)}</div>
          <div class="verdict-conf">Confidence: {confidence:.1%}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def confidence_ring(pct: float, is_phishing: bool) -> None:
    """Radial confidence gauge like Vite detect page."""
    color = "oklch(0.65 0.22 25)" if is_phishing else "oklch(0.74 0.14 158)"
    circumference = 2 * 3.14159 * 54
    offset = circumference - (pct / 100) * circumference
    st.markdown(
        f"""
        <div class="conf-ring-wrap">
          <div class="conf-ring">
            <svg width="140" height="140" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="54" fill="none" stroke="oklch(1 0 0 / 0.06)" stroke-width="10"/>
              <circle cx="60" cy="60" r="54" fill="none" stroke="{color}" stroke-width="10"
                stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                stroke-linecap="round"/>
            </svg>
            <div class="conf-ring-text">
              <span class="conf-ring-pct">{pct:.0f}%</span>
              <span class="conf-ring-label">Confidence</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_badge(level: str) -> None:
    """Risk level pill."""
    cls = f"risk-{level.lower()}"
    st.markdown(f'<span class="risk-badge {cls}">{html.escape(level)} risk</span>', unsafe_allow_html=True)


def shap_feature_bars(features: list[dict[str, Any]], max_items: int = 6) -> None:
    """Horizontal SHAP contribution bars (prefers plain-English labels)."""
    rows = []
    for f in features[:max_items]:
        weight = float(f.get("shap", f.get("weight", 0)))
        positive = weight > 0
        width_pct = min(abs(weight) / 0.5 * 50, 50)
        bar_cls = "shap-bar-fill-pos" if positive else "shap-bar-fill-neg"
        style = f"width:{width_pct}%;" + ("left:50%;" if positive else "right:50%;")
        val_cls = "shap-pos" if positive else "shap-neg"
        sign = "+" if positive else ""
        label = f.get("label") or f.get("feature") or f.get("name", "")
        rows.append(
            f"""<div class="shap-bar-row">
              <div class="shap-bar-name">{html.escape(str(label))}</div>
              <div class="shap-bar-track"><div class="{bar_cls}" style="{style}"></div></div>
              <div class="shap-bar-val {val_cls}">{sign}{weight:.2f}</div>
            </div>"""
        )
    st.markdown("".join(rows), unsafe_allow_html=True)


def anatomy_table(rows: list[tuple[str, str]]) -> None:
    """Styled URL anatomy table."""
    trs = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{html.escape(str(v))}</td></tr>" for k, v in rows
    )
    st.markdown(f'<table class="anatomy-table">{trs}</table>', unsafe_allow_html=True)


def confusion_matrix_html(tn: int, fp: int, fn: int, tp: int) -> None:
    """Confusion matrix grid matching Vite performance page."""
    st.markdown(
        f"""
        <div class="cm-grid">
          <div></div>
          <div class="cm-header">Pred. Legit</div>
          <div class="cm-header">Pred. Phish</div>
          <div class="cm-label">Actual Legit</div>
          <div class="cm-cell cm-cell-tn"><div class="cm-cell-num">{tn}</div><div class="cm-cell-tag">TN</div></div>
          <div class="cm-cell cm-cell-fp"><div class="cm-cell-num">{fp}</div><div class="cm-cell-tag">FP</div></div>
          <div class="cm-label">Actual Phish</div>
          <div class="cm-cell cm-cell-fn"><div class="cm-cell-num">{fn}</div><div class="cm-cell-tag">FN</div></div>
          <div class="cm-cell cm-cell-tp"><div class="cm-cell-num">{tp}</div><div class="cm-cell-tag">TP</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def narrative_box(text: str) -> None:
    """Human-readable explanation callout (supports markdown)."""
    st.markdown('<div class="narrative-box">', unsafe_allow_html=True)
    st.markdown("✨ **Plain-English explanation**")
    st.markdown(text)
    st.markdown("</div>", unsafe_allow_html=True)


def section_spacer(height: str = "1.5rem") -> None:
    """Vertical gap between Streamlit blocks (inner margins often collapse)."""
    st.markdown(
        f'<div class="section-spacer" style="height:{height};min-height:{height};"></div>',
        unsafe_allow_html=True,
    )


def source_card(name: str, count: str, note: str) -> None:
    """Dataset source card."""
    st.markdown(
        f"""
        <div class="source-card">
          <div class="source-card-title">{html.escape(name)}</div>
          <div class="source-card-count">{html.escape(count)}</div>
          <div class="source-card-note">{html.escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plotly_dark_layout() -> dict[str, Any]:
    """Shared Plotly dark theme."""
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#f4f6fb", "family": "Inter, sans-serif"},
        "margin": {"l": 20, "r": 20, "t": 40, "b": 20},
    }
