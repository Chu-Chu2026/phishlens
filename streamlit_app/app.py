"""
PhishLens — Explainable Ensemble ML Dashboard for Phishing URL Detection.

Run: streamlit run streamlit_app.py
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from streamlit_app.components.analysis import queue_analysis
from streamlit_app.components.ui import LOGO_SVG, init_landing_page
from streamlit_app.services.model_loader import load_metrics

init_landing_page("PhishLens — Explainable Phishing Detection", "🛡️")

metrics = load_metrics()
acc = f"{metrics.get('accuracy', 0):.1%}" if metrics else "—"
f1 = f"{metrics.get('f1', 0):.3f}" if metrics else "—"
auc = f"{metrics.get('auc', 0):.3f}" if metrics else "—"

# Sticky nav — single HTML flex row (Streamlit columns break vertical alignment)
st.markdown(
    f"""
    <header class="landing-top">
      <div class="landing-top-inner">
        <div class="landing-brand">
          <div class="sidebar-logo">{LOGO_SVG}</div>
          <span class="landing-brand-title">PhishLens</span>
          <span class="landing-brand-badge">Research</span>
        </div>
        <div class="landing-top-actions">
          <div class="landing-nav-scroll">
            <nav class="landing-nav-links" aria-label="Landing sections">
              <a href="#features">Features</a>
              <a href="#approach">Approach</a>
              <a href="#metrics">Metrics</a>
            </nav>
          </div>
          <a class="landing-dashboard-btn" href="Dashboard">Open dashboard →</a>
        </div>
      </div>
    </header>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="landing-nav-divider"></div>', unsafe_allow_html=True)

# Hero
st.markdown(
    """
    <section class="hero-bg landing-hero-wrap">
      <div class="landing-pill">✨ Explainable Ensemble ML · SHAP · Streamlit prototype</div>
      <h1 class="landing-h1">
        Phishing detection, <span class="gradient-text">made transparent.</span>
      </h1>
      <p class="landing-lead">
        Paste a suspicious URL below. PhishLens classifies it with an ensemble of
        Logistic Regression, Random Forest &amp; SVM — then opens the dashboard
        with SHAP explanations for every decision.
      </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="landing-input-wrap">', unsafe_allow_html=True)

with st.form("landing_analyze", clear_on_submit=False):
    url = st.text_input(
        "URL",
        placeholder="https://secure-login-microsft.com/verify",
        label_visibility="collapsed",
        key="landing_url_input",
    )
    submitted = st.form_submit_button("🔍 Analyze URL", type="primary", width="stretch")

st.page_link("pages/1_Dashboard.py", label="or skip straight to the dashboard →")

st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    if url and url.strip():
        queue_analysis(url.strip())
        st.switch_page("pages/1_Dashboard.py")
    else:
        st.warning("Enter a URL to analyze.")

# Features (before metrics — matches nav order)
st.markdown(
    """
    <section id="features" class="landing-features">
      <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--accent);">
        Why PhishLens
      </span>
      <h2 style="margin-top:0.75rem;font-size:clamp(1.75rem,4vw,2.25rem);font-weight:600;letter-spacing:-0.02em;">
        Trustworthy detection requires more than accuracy.
      </h2>
      <p style="margin-top:1rem;max-width:42rem;color:var(--muted-foreground);line-height:1.6;">
        Built for academic rigor, PhishLens pairs a high-performing ensemble classifier
        with SHAP-based interpretation so every prediction is inspectable, reproducible,
        and defensible.
      </p>
      <div class="landing-feature-grid">
        <div class="glass panel-card">
          <div class="landing-feature-icon">⚙️</div>
          <h3 style="margin-top:1.25rem;font-size:1.125rem;font-weight:600;">Ensemble model</h3>
          <p style="margin-top:0.5rem;font-size:0.875rem;color:var(--muted-foreground);line-height:1.6;">
            Logistic Regression, Random Forest and SVM combined via soft-voting
            for robust generalization.
          </p>
        </div>
        <div class="glass panel-card">
          <div class="landing-feature-icon">👁️</div>
          <h3 style="margin-top:1.25rem;font-size:1.125rem;font-weight:600;">SHAP explanations</h3>
          <p style="margin-top:0.5rem;font-size:0.875rem;color:var(--muted-foreground);line-height:1.6;">
            Per-feature contributions visualized with summary, waterfall, and force
            plots — no black boxes.
          </p>
        </div>
        <div class="glass panel-card">
          <div class="landing-feature-icon">🔒</div>
          <h3 style="margin-top:1.25rem;font-size:1.125rem;font-weight:600;">Research-grade</h3>
          <p style="margin-top:0.5rem;font-size:0.875rem;color:var(--muted-foreground);line-height:1.6;">
            Reproducible metrics, dataset analytics, and methodology suitable for
            dissertation evaluation.
          </p>
        </div>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section id="approach" class="landing-features" style="padding-top:2rem;">
      <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--accent);">
        Approach
      </span>
      <h2 style="margin-top:0.75rem;font-size:clamp(1.5rem,3vw,2rem);font-weight:600;">
        From URL to explainable verdict in one flow
      </h2>
      <ol class="landing-approach-list">
        <li>Normalize and featurize the submitted URL (34 lexical &amp; host signals)</li>
        <li>Classify with a soft-voting ensemble of three complementary learners</li>
        <li>Generate SHAP attributions and a human-readable analyst narrative</li>
        <li>Present results on the dashboard with evaluation-backed metrics</li>
      </ol>
    </section>
    """,
    unsafe_allow_html=True,
)

# Metrics preview
st.markdown('<section id="metrics">', unsafe_allow_html=True)
st.markdown('<div class="glass-strong" style="padding:0.5rem;border-radius:1.5rem;margin-top:1rem;">', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="landing-metric-grid" style="padding:1.5rem;">
      <div class="landing-metric-card">
        <div class="landing-metric-label">Accuracy</div>
        <div class="landing-metric-value">{html.escape(acc)}</div>
      </div>
      <div class="landing-metric-card">
        <div class="landing-metric-label">F1 Score</div>
        <div class="landing-metric-value">{html.escape(f1)}</div>
      </div>
      <div class="landing-metric-card">
        <div class="landing-metric-label">AUC</div>
        <div class="landing-metric-value">{html.escape(auc)}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div></section>", unsafe_allow_html=True)

st.markdown(
    """
    <footer class="landing-footer">
      <span>© 2026 PhishLens · Master's research prototype</span>
      <span>Built with Python · Streamlit · SHAP</span>
    </footer>
    """,
    unsafe_allow_html=True,
)

st.caption("All metrics loaded from evaluation/metrics.json — no fabricated data.")
