"""Dataset Analytics — corpus composition and feature distributions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_app.components.ui import (
    glass_panel,
    init_page,
    metrics_row,
    page_header,
    plotly_dark_layout,
    section_title,
    source_card,
)
from streamlit_app.services.model_loader import load_dataset_stats

init_page("Dataset Analytics · PhishLens", "🗄️", active_nav="dataset")

page_header(
    "Dataset Analytics",
    "Composition, balance, and feature distributions across the merged URL corpus.",
    badge="Corpus",
    accent=True,
)

stats = load_dataset_stats()
if not stats:
    st.warning("No dataset statistics found. Run the training pipeline first.")
    st.stop()

total = stats.get("total_urls", 0)
phish = stats.get("phishing_count", 0)
legit = stats.get("legitimate_count", 0)
feat_count = stats.get("feature_count", 0)

metrics_row([
    {"label": "Total URLs", "value": f"{total:,}", "icon_key": "urls"},
    {"label": "Legitimate", "value": f"{legit:,}", "sub": f"{100 * legit / max(total, 1):.0f}%", "icon_key": "legitimate"},
    {"label": "Phishing", "value": f"{phish:,}", "sub": f"{100 * phish / max(total, 1):.0f}%", "icon_key": "phishing"},
    {"label": "Features", "value": str(feat_count), "sub": "engineered", "icon_key": "features"},
])

col_pie, col_bar = st.columns([1, 2], gap="large")
layout = plotly_dark_layout()

with col_pie:
    with glass_panel():
        section_title("Class balance", "Near-uniform distribution")
        balance_df = pd.DataFrame({"class": ["Legitimate", "Phishing"], "count": [legit, phish]})
        fig = px.pie(
            balance_df,
            values="count",
            names="class",
            hole=0.45,
            color="class",
            color_discrete_map={"Legitimate": "#5ec995", "Phishing": "#e85d5d"},
        )
        fig.update_layout(**layout, showlegend=True, legend=dict(orientation="h", y=-0.1))
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, width="stretch")

with col_bar:
    with glass_panel():
        section_title("Feature distribution", "Normalized mean per class (0–1)")
        dist = stats.get("feature_distributions", [])
        if dist:
            dist_df = pd.DataFrame(dist)
            fig = px.bar(
                dist_df,
                x="name",
                y=["phishing", "legitimate"],
                barmode="group",
                color_discrete_map={"phishing": "#e85d5d", "legitimate": "#5ec995"},
            )
            fig.update_layout(**layout)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Feature distribution data not available. Re-run the training pipeline.")

with glass_panel():
    section_title("Sources")
    sources = stats.get("sources", {})
    if sources:
        items = list(sources.items())
        for row_start in range(0, len(items), 4):
            row_items = items[row_start : row_start + 4]
            src_cols = st.columns(len(row_items), gap="medium")
            notes = {
                "OpenPhish": "Live phishing feed",
                "BenignList": "Curated legitimate URLs",
                "PhiUSIIL": "Academic URL corpus",
                "Seed": "Offline development seed",
            }
            for col, (name, count) in zip(src_cols, row_items):
                with col:
                    source_card(name, f"{count:,}", notes.get(name, "Dataset source"))

st.caption("See data/DATASET.md for provenance, preprocessing, and split methodology.")
