# PhishLens

## Scroll down to view steps on how to deploy the artefact



**Explainable Ensemble Machine Learning Dashboard for Phishing URL Detection**

A Master's dissertation research prototype combining an ensemble of Logistic Regression, Random Forest, and SVM with SHAP explainability in a local Streamlit dashboard.


## Overview
![Loading Screen](/data/images/loading_screen.png)
![Dashboard](/data/images/img1.png)
![URL Analysis](/data/images/img2.png)
![Explainability](/data/images/img3.png)
![SHAP](/data/images/img4.png)


## Research Question

> Can an Explainable Ensemble Machine Learning model improve phishing URL detection while providing transparent explanations through SHAP?

## To view the deployed version of the project, please visit: [https://phishlens.streamlit.app/](https://phishlens.streamlit.app/)

### Note: Incase you see This app has gone to sleep due to inactivity. Please click on the blue button to wake it up. ![WAKE UP](/data/images/img5.png)


## Quick Start

### One-shot command to setup virtual environment and run the project (Recommended)

Copy and paste the command below into your terminal to installs dependencies, runs the ML pipeline, then launches Streamlit:

```bash
python scripts/setup_and_run.py
```

## OR


### Manual Setup Guide (if you want to know the details of the setup)
#### 1. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

#### 2. Run the ML pipeline (download → train → evaluate → SHAP)

```bash
python scripts/run_pipeline.py
```

Google Colab workflow: `notebooks/phishlens_colab.ipynb`

#### 3. Launch the dashboard

```bash
streamlit run streamlit_app.py
```

### Streamlit Community Cloud

1. Push this repo to GitHub.
2. At [share.streamlit.io](https://share.streamlit.io), deploy the repo.
3. Set **Main file path** to `streamlit_app.py` (not `scripts/setup_and_run.py`).
4. Use **Python 3.12** if the UI asks for a version (`runtime.txt` requests 3.12).

Cloud installs from `requirements.txt` automatically. Pre-trained models in `trained_models/` ship with the repo, so no training step is needed on Cloud.

**Loading screen note:** Streamlit paints a native skeleton *before* any Python/CSS runs. Locally, `scripts/patch_streamlit_splash.py` (run by `setup_and_run`) injects PhishLens branding into Streamlit’s `index.html` so the first paint is branded. Community Cloud often blocks that write — there you may still see a brief Streamlit skeleton, then the PhishLens splash. To hide the skeleton only: append `?embed=true&embed_options=hide_loading_screen` to the Cloud URL (also strips some chrome).

## Project Structure

```
phishlens/
├── streamlit_app.py        # Streamlit Cloud / local entrypoint
├── pages/                  # Multipage wrappers (Cloud discovers these next to entry)
├── streamlit_app/          # Streamlit dashboard (dissertation artefact)
│   ├── app.py
│   ├── pages/              # Dashboard, URL Analysis, Explainability, etc.
│   ├── services/           # Prediction, SHAP, model loading
│   └── utils/              # Feature extraction, URL validation
├── training/               # Offline ML pipeline
│   ├── download_data.py
│   ├── preprocess.py
│   ├── train.py
│   ├── evaluate.py
│   └── generate_shap.py
├── data/                   # Raw and processed datasets
├── trained_models/         # Serialized ensemble + metadata
├── evaluation/             # Metrics, plots, SHAP artifacts
├── tests/
├── src/                    # React UI (design reference only)
├── runtime.txt             # Python 3.12 for Streamlit Cloud
└── scripts/run_pipeline.py
```

## Ensemble Model

Soft-voting `VotingClassifier` over:

- Logistic Regression
- Random Forest
- Support Vector Machine (SVM)

## Explainability

SHAP `TreeExplainer` powers the charts, and every prediction also gets a **plain-English explanation** for non-technical users:

- Clear verdict (“risky” / “safer”) with confidence
- Everyday reasons (warning signs and reassuring signs)
- Practical advice on what to do next
- Global summary / importance plots plus per-URL waterfall and force-style charts

## Testing

```bash
pytest tests/ -v
```

## React UI (Design Reference)

The `src/` directory contains the original Lovable-generated React/TanStack Start UI. It uses mock data and is **not** the dissertation artefact. Use it as a visual design reference only.

```bash
npm install
npm run dev
```

## Academic Integrity

All metrics, plots, and SHAP values in the Streamlit app are computed from real model outputs. No fabricated evaluation results.

See `data/DATASET.md` for dataset provenance and methodology.

For dissertation writing support (paste-ready sections, results tables, limitations, and requirements traceability), see:

- `REPORT_WRITING_ARTIFACT.txt`
- `REPORT_WRITING_ARTIFACT.md`
- `REPORT_WRITING_ARTIFACT.pdf`
