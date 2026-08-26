"""
PhishLens — Streamlit Community Cloud entrypoint.

Deploy settings:
  Main file path: streamlit_app.py
  Python version: 3.12 (see runtime.txt)

Local:
  streamlit run streamlit_app.py

NOTE: This file is named streamlit_app.py while the package folder is also
streamlit_app/. Streamlit execs this file in a way that can shadow the package,
so boot imports loading.py by filesystem path (not via package import).
"""

from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _purge_streamlit_app_shadow() -> None:
    """Drop a shadowed/non-package ``streamlit_app`` module so the package wins."""
    mod = sys.modules.get("streamlit_app")
    if mod is None:
        return
    mod_file = Path(getattr(mod, "__file__", "") or "").resolve()
    # Entrypoint file or a non-package module occupying the name
    if mod_file == Path(__file__).resolve() or not hasattr(mod, "__path__"):
        for key in list(sys.modules):
            if key == "streamlit_app" or key.startswith("streamlit_app."):
                del sys.modules[key]


def _load_module_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# 0) Patch Streamlit's static index.html so the FIRST browser paint is branded.
#    Python splash alone cannot cover Streamlit's native skeleton (documented
#    limitation — CSS from st.markdown always arrives after that shell).
try:
    _patch = _load_module_from_path(
        "_phish_patch_streamlit_splash",
        ROOT / "scripts" / "patch_streamlit_splash.py",
    )
    _patch.patch_index()
except Exception:
    pass

_purge_streamlit_app_shadow()

# 1) Brand paint as soon as Python runs — load by path to avoid package-name shadowing
_loading = _load_module_from_path(
    "streamlit_app.components.loading",
    ROOT / "streamlit_app" / "components" / "loading.py",
)
_loading.boot_splash(
    title="PhishLens — Explainable Phishing Detection",
    icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2) Ensure package imports resolve to the directory package
_purge_streamlit_app_shadow()

# 3) Landing page (heavy imports run under the splash)
runpy.run_path(str(ROOT / "streamlit_app" / "app.py"), run_name="__main__")
