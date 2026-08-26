"""
Patch Streamlit's static index.html so PhishLens branding appears on first
browser paint — before React mounts and before any Python runs.

Why this is required
--------------------
Streamlit renders a native loading skeleton in the frontend *before* your
script executes. CSS/HTML from ``st.markdown`` always arrives too late, so a
Python-only splash cannot cover that first frame. Official docs only offer
``?embed=true&embed_options=hide_loading_screen`` (hides skeleton, no brand).
The supported community workaround for a *branded* first paint is to inject
into ``site-packages/streamlit/static/index.html`` (works locally / Docker;
Streamlit Community Cloud may block writes).

Idempotent: safe to run on every ``setup_and_run`` / app boot.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

MARKER = "<!-- phishlens-native-splash -->"

INJECTION = r"""
<!-- phishlens-native-splash -->
<style id="phishlens-native-splash-css">
  html, body, #root {
    background: #0b1020 !important;
    margin: 0;
    min-height: 100%;
  }
  /* Suppress Streamlit's native skeleton / chrome until our splash dismisses */
  [class*="Skeleton"],
  [data-testid="stSkeleton"],
  [data-testid="stDecoration"],
  [data-testid="stStatusWidget"],
  [data-testid="stToolbar"],
  header[data-testid="stHeader"] {
    opacity: 0 !important;
    visibility: hidden !important;
  }
  #phishlens-native-splash {
    position: fixed;
    inset: 0;
    z-index: 2147483646;
    display: grid;
    place-items: center;
    margin: 0;
    padding: 1rem;
    box-sizing: border-box;
    background:
      radial-gradient(900px 500px at 10% -10%, rgba(100, 149, 255, 0.2), transparent 60%),
      radial-gradient(800px 400px at 90% 0%, rgba(64, 200, 210, 0.14), transparent 60%),
      #0b1020;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    transition: opacity 0.45s ease, visibility 0.45s ease;
  }
  #phishlens-native-splash.phishlens-native-splash--hide {
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
  }
  #phishlens-native-splash .card {
    text-align: center;
    padding: 2rem 2.5rem;
    border-radius: 1.25rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
    box-shadow: 0 24px 60px -20px rgba(0, 0, 0, 0.7);
    min-width: 16rem;
  }
  #phishlens-native-splash .logo {
    width: 3rem;
    height: 3rem;
    margin: 0 auto 1rem;
    border-radius: 0.75rem;
    background: linear-gradient(135deg, #6ea8ff, #3ec8d2);
    display: grid;
    place-items: center;
    box-shadow: 0 12px 32px -8px rgba(110, 168, 255, 0.55);
  }
  #phishlens-native-splash .logo svg {
    display: block;
    width: 1.35rem;
    height: 1.35rem;
  }
  #phishlens-native-splash .title {
    font-size: 1.35rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #f4f6fb;
  }
  #phishlens-native-splash .sub {
    margin-top: 0.35rem;
    font-size: 0.8rem;
    color: #9aa3b5;
  }
  #phishlens-native-splash .ring {
    width: 1.75rem;
    height: 1.75rem;
    margin: 1.25rem auto 0;
    border-radius: 999px;
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-top-color: #6ea8ff;
    animation: phishlens-spin 0.75s linear infinite;
  }
  @keyframes phishlens-spin { to { transform: rotate(360deg); } }
</style>
<script id="phishlens-native-splash-js">
(function () {
  function mount() {
    if (document.getElementById("phishlens-native-splash")) return;
    var el = document.createElement("div");
    el.id = "phishlens-native-splash";
    el.setAttribute("aria-live", "polite");
    el.setAttribute("aria-busy", "true");
    el.innerHTML = '<div class="card">' +
      '<div class="logo"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0b1020" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></svg></div>' +
      '<div class="title">PhishLens</div>' +
      '<div class="sub">Explainable phishing detection</div>' +
      '<div class="ring" role="status"></div>' +
      '</div>';
    document.body.appendChild(el);
  }
  function hide() {
    var el = document.getElementById("phishlens-native-splash");
    if (!el || el.classList.contains("phishlens-native-splash--hide")) return;
    el.classList.add("phishlens-native-splash--hide");
    setTimeout(function () {
      if (el && el.parentNode) el.parentNode.removeChild(el);
    }, 500);
  }
  function ready() {
    // Python splash took over, or app signalled ready
    if (document.getElementById("phish-loader")) return true;
    if (document.getElementById("phish-app-ready")) return true;
    return false;
  }
  function watch() {
    if (ready()) { hide(); return; }
    var obs = new MutationObserver(function () {
      if (ready()) { hide(); obs.disconnect(); }
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
    // Safety: never block the UI forever if signals are missing
    setTimeout(function () { hide(); obs.disconnect(); }, 12000);
  }
  if (document.body) { mount(); watch(); }
  else {
    document.addEventListener("DOMContentLoaded", function () { mount(); watch(); });
  }
})();
</script>
"""


def streamlit_index_path() -> Path:
    import streamlit

    return Path(streamlit.__file__).resolve().parent / "static" / "index.html"


def is_patched(html: str) -> bool:
    return MARKER in html


def patch_index(index_path: Path | None = None, *, force: bool = False) -> str:
    """
    Inject native splash into Streamlit index.html.

    Returns: "patched" | "already" | "restored_and_patched"
    """
    path = index_path or streamlit_index_path()
    if not path.exists():
        raise FileNotFoundError(f"Streamlit index.html not found: {path}")

    html = path.read_text(encoding="utf-8")
    if is_patched(html) and not force:
        return "already"

    backup = path.with_suffix(".html.phishbak")
    if not backup.exists():
        shutil.copy2(path, backup)

    if is_patched(html) and force:
        # Restore from backup then re-apply
        html = backup.read_text(encoding="utf-8")
        status = "restored_and_patched"
    else:
        status = "patched"

    if "</head>" not in html:
        raise RuntimeError(f"Unexpected index.html (no </head>): {path}")

    # Prefer injecting before </head> so CSS applies ASAP; JS mounts on body.
    html = html.replace("</head>", INJECTION + "\n  </head>", 1)
    path.write_text(html, encoding="utf-8")
    return status


def unpatch_index(index_path: Path | None = None) -> str:
    path = index_path or streamlit_index_path()
    backup = path.with_suffix(".html.phishbak")
    if backup.exists():
        shutil.copy2(backup, path)
        return "restored"
    html = path.read_text(encoding="utf-8")
    if not is_patched(html):
        return "clean"
    raise RuntimeError("Patched index.html found but no .phishbak backup to restore")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Patch Streamlit index.html with PhishLens splash")
    parser.add_argument("--force", action="store_true", help="Re-apply even if already patched")
    parser.add_argument("--undo", action="store_true", help="Restore original index.html from backup")
    args = parser.parse_args(argv)

    try:
        if args.undo:
            result = unpatch_index()
        else:
            result = patch_index(force=args.force)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    path = streamlit_index_path()
    print(f"Streamlit index: {path}")
    print(f"Result: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
