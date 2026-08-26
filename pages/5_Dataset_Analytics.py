"""Cloud/local multipage wrapper → streamlit_app/pages/5_Dataset_Analytics.py"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.page_runner import run_page

run_page("5_Dataset_Analytics.py", title="Dataset Analytics · PhishLens", icon="🗄️")
