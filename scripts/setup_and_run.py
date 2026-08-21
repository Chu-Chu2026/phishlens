#!/usr/bin/env python3
"""
PhishLens one-shot launcher.

Creates a virtual environment (if needed), installs dependencies when missing,
runs the ML pipeline if models are missing, then starts Streamlit.

Usage:

    python scripts/setup_and_run.py

Common options:

    python scripts/setup_and_run.py --skip-install     # do not touch pip / venv packages
    python scripts/setup_and_run.py --skip-pipeline    # reuse existing trained models
    python scripts/setup_and_run.py --force-install    # always reinstall requirements
    python scripts/setup_and_run.py --force-pipeline   # always retrain
    python scripts/setup_and_run.py --run-tests
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Packages that must import successfully before we skip pip install
REQUIRED_IMPORTS = (
    "streamlit",
    "sklearn",
    "shap",
    "pandas",
    "numpy",
    "joblib",
    "matplotlib",
)


def _venv_python() -> Path:
    if os.name == "nt":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def _run(cmd: list[str], *, step: str) -> None:
    print(f"\n→ {step}")
    print(f"  {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=ROOT)
    except KeyboardInterrupt:
        print("\nCancelled by user.", file=sys.stderr)
        sys.exit(130)
    if result.returncode != 0:
        print(f"ERROR: {step} failed (exit code {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def _venv_has_deps(venv_py: Path) -> bool:
    """Return True if the venv can import the core PhishLens packages."""
    code = ";".join(f"import {name}" for name in REQUIRED_IMPORTS)
    probe = subprocess.run(
        [str(venv_py), "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return probe.returncode == 0


def _on_streamlit_cloud() -> bool:
    """True when this process is running inside Streamlit Community Cloud."""
    return Path("/mount/src").is_dir() or Path("/home/adminuser").is_dir()


def main() -> None:
    # Streamlit Cloud must use streamlit_app.py — this launcher creates a local .venv
    # and will fail there (no pip in Cloud's app .venv).
    if _on_streamlit_cloud():
        import streamlit as st

        st.set_page_config(page_title="PhishLens — fix deploy settings", page_icon="🛡️")
        st.error(
            "Wrong **Main file path** for Streamlit Community Cloud.\n\n"
            "In **App settings → General → Main file path**, set:\n\n"
            "`streamlit_app.py`"
        )
        st.info(
            "`scripts/setup_and_run.py` is a local installer/launcher only. "
            "It must not be the Cloud entrypoint."
        )
        st.stop()
        return

    parser = argparse.ArgumentParser(description="Install, train, and launch PhishLens.")
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip creating/updating the virtualenv and pip install.",
    )
    parser.add_argument(
        "--force-install",
        action="store_true",
        help="Always run pip install -r requirements.txt.",
    )
    parser.add_argument(
        "--skip-pipeline",
        action="store_true",
        help="Skip training if trained_models/ensemble.joblib already exists.",
    )
    parser.add_argument(
        "--force-pipeline",
        action="store_true",
        help="Always re-run the ML pipeline.",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run pytest before launching Streamlit.",
    )
    args = parser.parse_args()

    print("=" * 40)
    print("  PhishLens — setup & run")
    print("=" * 40)
    print(f"Project root: {ROOT}")
    print(f"Python: {sys.version.split()[0]}")

    venv_py = _venv_python()

    # 1) Virtual environment + dependencies
    if args.skip_install:
        if not venv_py.exists():
            print(
                "ERROR: --skip-install was set but .venv does not exist.\n"
                "Run once without --skip-install to create it.",
                file=sys.stderr,
            )
            sys.exit(1)
        print("\n→ Skipping install (--skip-install).")
    else:
        if not venv_py.exists():
            _run(
                [sys.executable, "-m", "venv", str(ROOT / ".venv")],
                step="Create virtual environment (.venv)",
            )
        else:
            print("\n→ Virtual environment already exists.")

        deps_ok = _venv_has_deps(venv_py)
        if deps_ok and not args.force_install:
            print("→ Core packages already installed — skipping pip install.")
            print("  (Use --force-install to reinstall requirements.txt)")
        else:
            if not deps_ok:
                print("→ Some packages are missing — installing requirements.txt …")
                print("  This can take a few minutes. Leave it running.")
            _run(
                [
                    str(venv_py),
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(ROOT / "requirements.txt"),
                ],
                step="Install requirements.txt",
            )
            if not _venv_has_deps(venv_py):
                print(
                    "ERROR: Packages still missing after install. "
                    "Try: .\\.venv\\Scripts\\python -m pip install -r requirements.txt",
                    file=sys.stderr,
                )
                sys.exit(1)

    # 2) ML pipeline
    model_path = ROOT / "trained_models" / "ensemble.joblib"
    if args.force_pipeline:
        run_pipeline = True
    elif args.skip_pipeline:
        run_pipeline = not model_path.exists()
        if run_pipeline:
            print("\n→ No trained model found; running pipeline anyway.")
        else:
            print("\n→ Skipping pipeline (--skip-pipeline); using existing models.")
    else:
        # Default: train only when model is missing
        run_pipeline = not model_path.exists()
        if run_pipeline:
            print("\n→ No trained model found — will run the ML pipeline.")
        else:
            print("\n→ Trained model found — skipping pipeline.")
            print("  (Use --force-pipeline to retrain)")

    if run_pipeline:
        _run(
            [str(venv_py), str(ROOT / "scripts" / "run_pipeline.py")],
            step="Run ML pipeline (download → train → evaluate → SHAP)",
        )

    # 3) Optional tests
    if args.run_tests:
        _run(
            [str(venv_py), "-m", "pytest", str(ROOT / "tests"), "-v"],
            step="Run tests",
        )

    # 4) Launch Streamlit
    print("\n→ Launching Streamlit dashboard…")
    print("  Open the URL shown below (usually http://localhost:8501)")
    print("  Press Ctrl+C to stop the app.\n")
    app_path = ROOT / "streamlit_app.py"
    try:
        result = subprocess.run(
            [str(venv_py), "-m", "streamlit", "run", str(app_path)],
            cwd=ROOT,
        )
    except KeyboardInterrupt:
        print("\nStreamlit stopped.")
        sys.exit(0)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
