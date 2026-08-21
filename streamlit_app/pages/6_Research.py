"""Research documentation — objectives, methodology, limitations."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from streamlit_app.components.ui import init_page, metrics_row, page_header
from streamlit_app.services.model_loader import load_metadata, load_metrics

init_page("Research · PhishLens", "📚", active_nav="research")

metrics = load_metrics()
meta = load_metadata()

page_header(
    "Research documentation",
    "Methodology, evaluation, and limitations for the dissertation artefact.",
    badge="Technical report",
    accent=True,
)

if metrics:
    metrics_row([
        {"label": "Accuracy", "value": f"{metrics.get('accuracy', 0):.1%}", "icon_key": "accuracy"},
        {"label": "F1 Score", "value": f"{metrics.get('f1', 0):.3f}", "icon_key": "f1"},
        {"label": "AUC", "value": f"{metrics.get('auc', 0):.3f}", "icon_key": "auc"},
        {"label": "Test size", "value": str(metrics.get("test_size", "—")), "icon_key": "test"},
    ])

sections = [
    ("Research question", """
**Can explainable ensemble machine learning improve phishing URL detection while providing
transparent SHAP-based explanations that support analyst interpretation?**

This artefact answers the question through a functional Streamlit prototype, offline model
evaluation, and interpretability visualisations — not production deployment.
    """),
    ("Research Objectives", """
- Build a phishing URL classifier with strong performance on a balanced corpus.
- Combine Logistic Regression, Random Forest, and SVM into a soft-voting ensemble.
- Quantify and visualize each prediction with SHAP for interpretability.
- Deliver a local Streamlit prototype suitable for dissertation demonstration.
    """),
    ("Methodology", f"""
URLs are normalized and converted into a **{meta.get('feature_count', 34)}-dimensional**
feature vector spanning lexical and host-based signals. Class imbalance is mitigated
via stratified sampling. The dataset is split 60/20/20 (train/validation/test).

Final evaluation uses the held-out test set (n = {metrics.get('test_size', '—')}).
Metrics include accuracy, precision, recall, F1, AUC, and inference latency.
Automated software tests cover feature extraction, URL validation, and prediction/SHAP integration.
    """),
    ("Ensemble Models", """
| Model | Role |
|-------|------|
| Logistic Regression | Linear probabilistic baseline |
| Random Forest | Bagged trees · variance reduction |
| Support Vector Machine (RBF) | Non-linear margin classifier with probability calibration |
| Voting Classifier | Soft-vote aggregation of all three |
    """),
    ("SHAP Explainability", """
SHAP values are computed with **TreeExplainer** on the Random Forest base learner — the first
estimator in the soft-voting ensemble — as a computationally tractable proxy for local
attributions. The dashboard surfaces global summary, per-prediction waterfall, ranked
importance, force plots, and human-readable narratives from top contributors.

*Note for examiners:* ensemble-level SHAP is an open research trade-off; the dissertation
should discuss proxy explainability vs. explaining the full voting function.
    """),
    (
        "Results",
        f"""
On the held-out test set, the ensemble achieved:
- **Accuracy:** {metrics.get('accuracy', 0):.1%}
- **Precision:** {metrics.get('precision', 0):.1%}
- **Recall:** {metrics.get('recall', 0):.1%}
- **F1 Score:** {metrics.get('f1', 0):.3f}
- **AUC:** {metrics.get('auc', 0):.3f}
- **Inference latency (p95):** {metrics.get('latency', {}).get('p95_ms', 0):.1f} ms

Results include per-model comparison and ensemble outcomes on the held-out test split.
        """
        if metrics
        else "Run `python scripts/run_pipeline.py` to generate evaluation results."
    ),
    ("Limitations", """
- URL-only features cannot capture page content or visual deception.
- Corpus size (~500 URLs) is small relative to production phishing studies.
- Perfect test metrics warrant cautious interpretation and external validation.
- Concept drift in phishing campaigns requires periodic retraining.
- SHAP attributions explain the model, not ground-truth causality.
- No formal large-sample user study is included yet to quantify confidence gains at scale.
    """),
    ("Future Work", """
- Fuse URL features with rendered DOM and screenshot embeddings.
- Analyst-in-the-loop feedback for model refinement.
- Adversarial robustness evaluation against URL-perturbation attacks.
- Scale dataset with PhiUSIIL and additional academic corpora.
    """),
    ("Key references", """
- Lundberg, S. M., & Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions* (SHAP).
- Breiman, L. (2001). Random Forests. *Machine Learning*.
- Cortes, C., & Vapnik, V. (1995). Support-Vector Networks. *Machine Learning*.
- Hosmer, D. W., Lemeshow, S., & Sturdivant, R. X. (2013). *Applied Logistic Regression*.
- Radharapu, B. K., et al. (2024). PhiUSIIL Phishing URL Dataset (academic corpus).
- OpenPhish community feed (live phishing URLs).

Cite these and related phishing-URL feature literature in your dissertation chapter.
    """),
]

for title, body in sections:
    with st.expander(title, expanded=title in ("Research question", "Results")):
        st.markdown(body)

st.caption("PhishLens · Research prototype · All metrics computed from real evaluation artifacts.")
