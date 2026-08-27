# PhishLens

**Explainable Ensemble Machine Learning Dashboard for Phishing URL Detection**

A Master's dissertation research prototype combining an ensemble of Logistic Regression, Random Forest, and SVM with SHAP explainability in a local Streamlit dashboard.

## Overview

Loading Screen
Dashboard
URL Analysis
Explainability
SHAP

## Research Question

> Can an Explainable Ensemble Machine Learning model improve phishing URL detection while providing transparent explanations through SHAP?

## To view the deployed version of the project, please visit: [https://phishlens.streamlit.app/](https://phishlens.streamlit.app/)

### Note: Incase you see This app has gone to sleep due to inactivity. Please click on the blue button to wake it up. ![WAKE UP](/data/images/img5.png) 




## Quick Start


### One-shot Command to Setup virtual environment and run the project (Recommended)

Creates `.venv`, installs dependencies, runs the ML pipeline, then launches Streamlit:

```bash
python scripts/setup_and_run.py
```

Options:

```bash
python scripts/setup_and_run.py --skip-install      # don't touch pip
python scripts/setup_and_run.py --skip-pipeline     # don't retrain
python scripts/setup_and_run.py --force-install     # reinstall requirements
python scripts/setup_and_run.py --force-pipeline    # retrain models
python scripts/setup_and_run.py --run-tests
```

The script skips pip install and training when `.venv` packages and `trained_models/ensemble.joblib` already exist.

(`scripts/setup_and_run.ps1` / `.bat` are optional Windows wrappers around the same flow.)

### Manual Project Setup and Execution



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
streamlit run streamlit_app/app.py
```



## Project Structure

```
phishlens/
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

