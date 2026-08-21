"""Confidence Evidence — capture pre/post explainability confidence ratings."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from streamlit_app.components.ui import glass_panel, init_page, metrics_row, page_header, section_title

DATA_PATH = ROOT / "evaluation" / "user_confidence.json"


def _load_rows() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_rows(rows: list[dict]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def _compute_summary(rows: list[dict]) -> dict[str, float]:
    if not rows:
        return {"n": 0, "before": 0.0, "after": 0.0, "delta": 0.0}
    before = [float(r["confidence_before"]) for r in rows]
    after = [float(r["confidence_after"]) for r in rows]
    before_mean = float(sum(before) / len(before))
    after_mean = float(sum(after) / len(after))
    return {
        "n": float(len(rows)),
        "before": before_mean,
        "after": after_mean,
        "delta": after_mean - before_mean,
    }


init_page("Confidence Evidence · PhishLens", "🧪", active_nav="confidence")

page_header(
    "User Confidence Evidence",
    "After reading the plain-English explanation, record whether your confidence went up. "
    "This creates evidence that explainability helps people trust (or question) the result.",
    badge="Evaluation",
    accent=True,
)

rows = _load_rows()
summary = _compute_summary(rows)

metrics_row([
    {"label": "Samples", "value": str(int(summary["n"])), "icon_key": "test"},
    {"label": "Mean confidence (before)", "value": f"{summary['before']:.2f}/5", "icon_key": "recall"},
    {"label": "Mean confidence (after)", "value": f"{summary['after']:.2f}/5", "icon_key": "accuracy"},
    {"label": "Mean uplift", "value": f"{summary['delta']:+.2f}", "icon_key": "f1"},
])

with glass_panel():
    section_title("Add an observation", "Use immediately after completing a URL analysis")
    with st.form("confidence_form", clear_on_submit=True):
        analyst_id = st.text_input("Participant / Analyst ID", placeholder="P01")
        confidence_before = st.slider(
            "Confidence BEFORE seeing SHAP explanation (1-5)",
            min_value=1,
            max_value=5,
            value=3,
        )
        confidence_after = st.slider(
            "Confidence AFTER seeing SHAP explanation (1-5)",
            min_value=1,
            max_value=5,
            value=4,
        )
        url_pred = st.selectbox("Prediction label shown", options=["Phishing", "Legitimate"])
        notes = st.text_area("Optional notes", placeholder="Why confidence changed (or did not).")
        submitted = st.form_submit_button("Save observation", type="primary", width="stretch")

    if submitted:
        if not analyst_id.strip():
            st.warning("Enter a participant/analyst ID.")
        else:
            rows.append({
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "analyst_id": analyst_id.strip(),
                "prediction_label": url_pred,
                "confidence_before": int(confidence_before),
                "confidence_after": int(confidence_after),
                "delta": int(confidence_after) - int(confidence_before),
                "notes": notes.strip(),
            })
            _save_rows(rows)
            st.success("Observation saved.")
            st.rerun()

with glass_panel():
    section_title("Recorded observations", "Stored in evaluation/user_confidence.json")
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No observations yet. Add your first confidence record above.")

