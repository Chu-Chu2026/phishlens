"""Central configuration for PhishLens training and evaluation."""

from __future__ import annotations

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "trained_models"
EVAL_DIR = PROJECT_ROOT / "evaluation"
PLOTS_DIR = EVAL_DIR / "plots"
SHAP_DIR = EVAL_DIR / "shap"

# Reproducibility
RANDOM_STATE = 42

# Dataset split ratios (train / val / test)
TRAIN_RATIO = 0.6
VAL_RATIO = 0.2
TEST_RATIO = 0.2

# Labels
LABEL_PHISHING = 1
LABEL_LEGITIMATE = 0
LABEL_NAMES = {0: "Legitimate", 1: "Phishing"}

# Risk thresholds (phishing probability)
RISK_THRESHOLDS = {
    "Low": (0.0, 0.30),
    "Medium": (0.30, 0.60),
    "High": (0.60, 0.85),
    "Critical": (0.85, 1.01),
}

# Ensemble base learners
ENSEMBLE_MODELS = ("logistic_regression", "random_forest", "svm")

# SHAP sample size for global explanations
SHAP_BACKGROUND_SIZE = 200
SHAP_TEST_SAMPLE_SIZE = 500

# Public dataset sources (documented in data/DATASET.md)
OPENPHISH_FEED_URL = "https://openphish.com/feed.txt"
PHIUSIIL_MIRROR_URL = (
    "https://raw.githubusercontent.com/urwithajit9/Clf_SURL/master/"
    "Data/PhiUSIIL_Phishing_URL_Dataset.csv"
)
BENIGN_URLS_URL = (
    "https://raw.githubusercontent.com/dhamodharanr/phishing-dataset/"
    "master/legitimate_urls.csv"
)
