"""Run a streamlit_app/pages/*.py module after early boot."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def run_page(page_filename: str, *, title: str, icon: str) -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    import streamlit as st

    from streamlit_app.components.loading import inject_loading_screen

    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_loading_screen()

    runpy.run_path(
        str(root / "streamlit_app" / "pages" / page_filename),
        run_name="__main__",
    )
