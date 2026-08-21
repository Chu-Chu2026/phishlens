"""Model Evaluation — metrics and diagnostic plots."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from streamlit_app.components.ui import (
    confusion_matrix_html,
    glass_panel,
    init_page,
    metrics_row,
    page_header,
    plot_placeholder,
    section_title,
)
from streamlit_app.services.model_loader import get_plot_path, load_metrics

init_page("Model Evaluation · PhishLens", "📈", active_nav="performance")

page_header(
    "Model Performance",
    "Held-out test set metrics and diagnostic plots for the ensemble model.",
    badge="Evaluation",
    accent=True,
)

metrics = load_metrics()
if not metrics:
    st.warning("No evaluation metrics found. Run: `python scripts/run_pipeline.py`")
    st.stop()

metrics_row([
    {"label": "Accuracy", "value": f"{metrics['accuracy']:.1%}", "icon_key": "accuracy"},
    {"label": "Precision", "value": f"{metrics.get('precision', 0):.1%}", "icon_key": "precision"},
    {"label": "Recall", "value": f"{metrics.get('recall', 0):.1%}", "icon_key": "recall"},
    {"label": "F1 Score", "value": f"{metrics['f1']:.3f}", "icon_key": "f1"},
    {"label": "AUC", "value": f"{metrics['auc']:.3f}", "icon_key": "auc"},
    {"label": "Latency p95", "value": f"{metrics.get('latency', {}).get('p95_ms', 0):.1f} ms", "icon_key": "latency"},
])

col_cm, col_roc = st.columns(2, gap="large")

with col_cm:
    with glass_panel():
        section_title("Confusion Matrix", f"Test split (n = {metrics.get('test_size', '—')})")
        cm = metrics.get("confusion_matrix", [[0, 0], [0, 0]])
        if len(cm) == 2:
            confusion_matrix_html(cm[0][0], cm[0][1], cm[1][0], cm[1][1])

with col_roc:
    with glass_panel():
        section_title("ROC Curve", f"AUC = {metrics.get('auc', 0):.3f}")
        roc_path = get_plot_path("roc_curve.png")
        if roc_path.exists():
            st.image(str(roc_path), width="stretch")
        else:
            plot_placeholder("ROC curve")

col_pr, col_cmp = st.columns(2, gap="large")

with col_pr:
    with glass_panel():
        section_title("Precision–Recall Curve", f"AP = {metrics.get('average_precision', 0):.3f}")
        pr_path = get_plot_path("pr_curve.png")
        if pr_path.exists():
            st.image(str(pr_path), width="stretch")
        else:
            plot_placeholder("Precision–Recall curve")

with col_cmp:
    with glass_panel():
        section_title("Model Comparison", "Accuracy & F1 across candidates")
        comp_path = get_plot_path("model_comparison.png")
        if comp_path.exists():
            st.image(str(comp_path), width="stretch")
        comparison = metrics.get("model_comparison", [])
        if comparison:
            st.dataframe(pd.DataFrame(comparison), width="stretch", hide_index=True)
        elif not comp_path.exists():
            plot_placeholder("Model comparison chart")

st.caption(
    f"Held-out test set · Precision {metrics.get('precision', 0):.3f} · "
    f"Recall {metrics.get('recall', 0):.3f} · F1 {metrics.get('f1', 0):.3f}"
)
