"""
PhishLens — Streamlit Community Cloud entrypoint.

Deploy settings:
  Main file path: streamlit_app.py
  Python version: 3.12 (see runtime.txt)

Local:
  streamlit run streamlit_app.py
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runpy.run_path(str(ROOT / "streamlit_app" / "app.py"), run_name="__main__")
