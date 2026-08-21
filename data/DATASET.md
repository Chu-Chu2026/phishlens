# PhishLens Dataset Documentation

## Overview

PhishLens uses a merged corpus of labelled phishing and legitimate URLs from public academic and threat-intelligence sources. All preprocessing, splitting, and feature engineering are documented here for reproducibility.

## Sources

| Source | Description | Label |
|--------|-------------|-------|
| **PhiUSIIL** | Academic phishing URL dataset (Mendeley / mirror) | Mixed |
| **OpenPhish** | Live phishing feed | Phishing (1) |
| **Benign URL list** | Curated legitimate domains | Legitimate (0) |

If remote downloads fail, a minimal seed dataset is used for offline development (see `training/download_data.py`).

## Preprocessing

1. **Download** — `python -m training.download_data`
2. **Clean** — strip whitespace, remove duplicates, drop invalid URLs
3. **Deduplicate** — unique by URL string
4. **Stratified split** — 60% train / 20% validation / 20% test (`random_state=42`)

Splits are saved to `data/processed/{train,val,test,full}.csv`.

## Feature Engineering

34 lexical and host-based features are extracted per URL (see `streamlit_app/utils/feature_extraction.py`):

- Length features (URL, hostname, path, query)
- Character counts (dots, hyphens, digits, special chars)
- Structural features (subdomains, path depth, query params)
- Security indicators (HTTPS, IP host, @ symbol)
- Suspicious keyword and TLD flags
- Entropy measures
- Brand impersonation heuristic

**No label information is used during feature extraction** (no leakage).

## Evaluation Methodology

- Models trained on **train** split only
- Hyperparameter validation on **val** split (optional tuning)
- Final metrics reported on **test** split only
- SHAP global plots computed on a stratified sample of the test set
- Inference latency measured per-URL on test sample

## Reproducibility

```bash
python scripts/run_pipeline.py
```

This regenerates all artifacts in `trained_models/`, `evaluation/`, and `data/processed/`.
