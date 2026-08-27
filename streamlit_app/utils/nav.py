"""Streamlit multipage paths relative to the Cloud/local entrypoint ``streamlit_app.py``."""

from __future__ import annotations

# Entrypoint file (repo root). Must match `streamlit run …` / Cloud Main file path.
HOME_PAGE = "streamlit_app.py"

DASHBOARD = "pages/1_Dashboard.py"
URL_ANALYSIS = "pages/2_URL_Analysis.py"
EXPLAINABILITY = "pages/3_Explainability.py"
MODEL_EVALUATION = "pages/4_Model_Evaluation.py"
DATASET_ANALYTICS = "pages/5_Dataset_Analytics.py"
RESEARCH = "pages/6_Research.py"
CONFIDENCE_EVIDENCE = "pages/7_Confidence_Evidence.py"
