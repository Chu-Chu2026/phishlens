"""Cloud/local multipage wrapper → streamlit_app/pages/7_Confidence_Evidence.py"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runpy.run_path(
    str(ROOT / "streamlit_app" / "pages" / "7_Confidence_Evidence.py"),
    run_name="__main__",
)
