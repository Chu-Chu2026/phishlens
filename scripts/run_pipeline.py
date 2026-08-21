"""End-to-end training and evaluation pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from training.dataset_stats import generate_dataset_stats
from training.download_data import download_all
from training.evaluate import evaluate
from training.generate_shap import generate_shap_artifacts
from training.preprocess import preprocess
from training.train import train

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Run full PhishLens ML pipeline."""
    logger.info("=== PhishLens Pipeline ===")

    logger.info("Step 1/6: Downloading datasets...")
    download_all()

    logger.info("Step 2/6: Preprocessing...")
    preprocess()

    logger.info("Step 3/6: Training ensemble...")
    train()

    logger.info("Step 4/6: Evaluating on test set...")
    metrics = evaluate()
    logger.info(
        "Test metrics — Acc: %.4f, F1: %.4f, AUC: %.4f",
        metrics["accuracy"],
        metrics["f1"],
        metrics["auc"],
    )

    logger.info("Step 5/6: Generating SHAP artifacts...")
    generate_shap_artifacts()

    logger.info("Step 6/6: Generating dataset statistics...")
    generate_dataset_stats()

    logger.info("=== Pipeline complete ===")
    logger.info("Run: streamlit run streamlit_app/app.py")


if __name__ == "__main__":
    main()
