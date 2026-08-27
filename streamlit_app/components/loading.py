"""Full-screen loading splash for PhishLens.

Boot as early as possible (before heavy imports). The splash stays opaque until
``dismiss_loading_screen()`` runs after page chrome is ready.
"""

from __future__ import annotations

import streamlit as st

_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
  fill="none" stroke="#0b1020" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
  <path d="m9 12 2 2 4-4"/>
</svg>
"""

_SPLASH_MARKUP = f"""
<style>
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stSidebar"],
section.main {{
  background: #0b1020 !important;
}}

[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"],
[data-testid="stSidebar"] {{
  opacity: 0 !important;
}}

#phish-loader {{
  position: fixed;
  inset: 0;
  z-index: 2147483647;
  display: grid;
  place-items: center;
  margin: 0;
  padding: 1rem;
  box-sizing: border-box;
  background:
    radial-gradient(900px 500px at 10% -10%, rgba(100, 149, 255, 0.2), transparent 60%),
    radial-gradient(800px 400px at 90% 0%, rgba(64, 200, 210, 0.14), transparent 60%),
    #0b1020;
  opacity: 1;
  visibility: visible;
  pointer-events: none;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}}

@keyframes phish-loader-fade {{
  0% {{ opacity: 1; visibility: visible; }}
  100% {{ opacity: 0; visibility: hidden; }}
}}

#phish-loader .phish-loader-card {{
  text-align: center;
  padding: 2rem 2.5rem;
  border-radius: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 24px 60px -20px rgba(0, 0, 0, 0.7);
  min-width: 16rem;
}}

#phish-loader .phish-loader-logo {{
  width: 3rem;
  height: 3rem;
  margin: 0 auto 1rem;
  border-radius: 0.75rem;
  background: linear-gradient(135deg, #6ea8ff, #3ec8d2);
  display: grid;
  place-items: center;
  box-shadow: 0 12px 32px -8px rgba(110, 168, 255, 0.55);
}}

#phish-loader .phish-loader-logo svg {{
  display: block;
  width: 1.35rem;
  height: 1.35rem;
}}

#phish-loader .phish-loader-title {{
  font-size: 1.35rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: #f4f6fb;
}}

#phish-loader .phish-loader-sub {{
  margin-top: 0.35rem;
  font-size: 0.8rem;
  color: #9aa3b5;
}}

#phish-loader .phish-loader-ring {{
  width: 1.75rem;
  height: 1.75rem;
  margin: 1.25rem auto 0;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top-color: #6ea8ff;
  animation: phish-spin 0.75s linear infinite;
}}

@keyframes phish-spin {{
  to {{ transform: rotate(360deg); }}
}}
</style>
<div id="phish-loader" aria-live="polite" aria-busy="true">
  <div class="phish-loader-card">
    <div class="phish-loader-logo">{_LOGO_SVG.strip()}</div>
    <div class="phish-loader-title">PhishLens</div>
    <div class="phish-loader-sub">Explainable phishing detection</div>
    <div class="phish-loader-ring" role="status"></div>
  </div>
</div>
"""


def boot_splash(
    *,
    title: str = "PhishLens — Explainable Phishing Detection",
    icon: str = "🛡️",
    layout: str = "wide",
    initial_sidebar_state: str = "collapsed",
) -> None:
    """Earliest branded paint: set_page_config + splash. Call before heavy imports."""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state,
    )
    inject_loading_screen()


def inject_loading_screen() -> None:
    """Show branded splash once per browser session (stays until dismiss)."""
    if st.session_state.get("_phish_loader_done"):
        return
    st.session_state._phish_loader_done = True
    st.session_state._phish_loader_visible = True
    st.markdown(_SPLASH_MARKUP, unsafe_allow_html=True)


def dismiss_loading_screen() -> None:
    """Fade Python splash after page chrome is ready; signal native splash to exit."""
    if not st.session_state.get("_phish_loader_visible"):
        # Still emit ready marker so a native-only splash can dismiss
        st.markdown(
            '<div id="phish-app-ready" style="display:none" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        return
    st.session_state._phish_loader_visible = False
    st.markdown(
        """
<div id="phish-app-ready" style="display:none" aria-hidden="true"></div>
<style>
#phish-loader { animation: phish-loader-fade 0.5s ease forwards; }
@keyframes phish-loader-fade {
  0% { opacity: 1; visibility: visible; }
  100% { opacity: 0; visibility: hidden; }
}
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"],
[data-testid="stSidebar"] {
  opacity: 1 !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def safe_set_page_config(**kwargs) -> None:
    """No-op if set_page_config was already called in this script run."""
    try:
        st.set_page_config(**kwargs)
    except Exception:
        pass
