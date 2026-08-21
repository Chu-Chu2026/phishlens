"""SHAP explainability service with plain-English narratives."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from streamlit_app.services.model_loader import load_shap_explainer
from streamlit_app.utils.feature_extraction import FEATURE_NAMES, extract_features_dataframe

# Technical feature → plain-English label + why it matters for phishing risk
FEATURE_GUIDE: dict[str, dict[str, str]] = {
    "url_length": {
        "label": "Overall link length",
        "risk": "Unusually long links are often used to hide where you are really going.",
        "safe": "The link length looks typical for a normal website.",
    },
    "hostname_length": {
        "label": "Website name length",
        "risk": "A very long website name can be a sign of a made-up or deceptive address.",
        "safe": "The website name length looks normal.",
    },
    "path_length": {
        "label": "Page path length",
        "risk": "A long, complicated path after the website name can hide a scam page.",
        "safe": "The page path length does not look suspicious on its own.",
    },
    "query_length": {
        "label": "Extra parameters in the link",
        "risk": "Lots of hidden parameters can be used to track you or disguise a phishing page.",
        "safe": "There are not many extra parameters tucked into this link.",
    },
    "num_dots": {
        "label": "Number of dots in the address",
        "risk": "Many dots can mean nested subdomains that try to look like a trusted brand.",
        "safe": "The number of dots in the address looks ordinary.",
    },
    "num_hyphens": {
        "label": "Hyphens in the address",
        "risk": "Scam sites often add hyphens to imitate real brands (for example paypal-secure-login).",
        "safe": "Hyphen use in this address does not look unusual.",
    },
    "num_underscores": {
        "label": "Underscores in the address",
        "risk": "Unusual underscores can appear in obfuscated phishing URLs.",
        "safe": "Underscore use does not stand out here.",
    },
    "num_slashes": {
        "label": "Number of path segments",
        "risk": "A deep folder structure can hide a fake login page further down the link.",
        "safe": "The path structure looks fairly simple.",
    },
    "num_digits": {
        "label": "Digits in the address",
        "risk": "Lots of numbers in a website address are common in throwaway scam domains.",
        "safe": "Digit use in this address looks normal.",
    },
    "num_special_chars": {
        "label": "Unusual symbols",
        "risk": "Odd symbols can be used to confuse people or bypass filters.",
        "safe": "There are few unusual symbols in this link.",
    },
    "subdomain_count": {
        "label": "Extra prefixes before the main site name",
        "risk": "Extra prefixes (like login.secure.example.com) are a common phishing trick.",
        "safe": "There are few or no extra prefixes before the main site name.",
    },
    "path_depth": {
        "label": "How deep the page is nested",
        "risk": "Deep nesting can hide a fake page under many folders.",
        "safe": "The page is not buried unusually deep.",
    },
    "query_param_count": {
        "label": "Number of query parameters",
        "risk": "Many query parameters can disguise tracking or phishing payloads.",
        "safe": "The number of query parameters looks modest.",
    },
    "has_https": {
        "label": "Uses a secure HTTPS connection",
        "risk": "Missing HTTPS (or weak signalling around it) can increase risk.",
        "safe": "The link uses HTTPS, which is a basic safety sign — though not a guarantee.",
    },
    "has_http": {
        "label": "Uses plain HTTP (not encrypted)",
        "risk": "A non-encrypted HTTP link is easier for attackers to abuse.",
        "safe": "The link is not relying on plain HTTP.",
    },
    "has_at_symbol": {
        "label": "Contains an @ symbol",
        "risk": "An @ in a URL can trick browsers into showing a fake site name.",
        "safe": "There is no @ trick in this address.",
    },
    "has_ip_host": {
        "label": "Uses a raw IP address instead of a name",
        "risk": "Legitimate brands rarely ask you to visit a raw number address (like 192.168…).",
        "safe": "This link uses a normal website name, not a raw IP address.",
    },
    "has_port": {
        "label": "Non-standard network port",
        "risk": "Odd ports can point to unofficial or temporary scam servers.",
        "safe": "No unusual port number stands out.",
    },
    "has_double_slash_redirect": {
        "label": "Double-slash redirect pattern",
        "risk": "Redirect-style patterns can send you somewhere different from what you expect.",
        "safe": "No double-slash redirect pattern was flagged.",
    },
    "suspicious_keyword_count": {
        "label": "Scam-style words in the link",
        "risk": "Words like login, verify, secure, update, or wallet often appear in phishing lures.",
        "safe": "Few scam-style keywords appear in this link.",
    },
    "has_suspicious_keyword": {
        "label": "Contains common scam wording",
        "risk": "This link includes wording frequently used to rush people into logging in.",
        "safe": "Common scam wording was not strongly present.",
    },
    "is_suspicious_tld": {
        "label": "Unusual website ending (TLD)",
        "risk": "Some endings (like .xyz, .tk, .top) are more often abused by scammers.",
        "safe": "The website ending does not look like a commonly abused scam TLD.",
    },
    "tld_length": {
        "label": "Length of the website ending",
        "risk": "An unusual ending length can accompany obscure scam domains.",
        "safe": "The website ending length looks ordinary.",
    },
    "digit_ratio_hostname": {
        "label": "How number-heavy the site name is",
        "risk": "Site names packed with numbers are often cheap throwaway domains.",
        "safe": "The site name is not unusually number-heavy.",
    },
    "letter_ratio_hostname": {
        "label": "How letter-based the site name is",
        "risk": "An odd mix of letters can signal an automatically generated scam domain.",
        "safe": "The site name looks mostly like ordinary wording.",
    },
    "hostname_entropy": {
        "label": "Random-looking website name",
        "risk": "A random-looking site name is common for short-lived phishing domains.",
        "safe": "The website name does not look especially random.",
    },
    "path_entropy": {
        "label": "Random-looking page path",
        "risk": "A garbled path can hide generated phishing pages.",
        "safe": "The page path does not look unusually random.",
    },
    "url_entropy": {
        "label": "Overall randomness of the link",
        "risk": "Highly random-looking links are often machine-generated phishing URLs.",
        "safe": "Overall, the link does not look unusually random.",
    },
    "long_url": {
        "label": "Marked as a long link",
        "risk": "Long links make it harder to see the real destination at a glance.",
        "safe": "The link was not flagged as unusually long.",
    },
    "very_long_url": {
        "label": "Marked as a very long link",
        "risk": "Very long links are a classic way to bury the real destination.",
        "safe": "The link was not flagged as extremely long.",
    },
    "short_hostname": {
        "label": "Very short website name",
        "risk": "Extremely short or odd host names can be disposable scam domains.",
        "safe": "The website name length looks reasonable.",
    },
    "many_subdomains": {
        "label": "Many prefixes before the main site",
        "risk": "Multiple prefixes are often used to impersonate banks or tech brands.",
        "safe": "There are not many prefixes before the main site name.",
    },
    "many_hyphens": {
        "label": "Many hyphens in the site name",
        "risk": "Lots of hyphens often appear in lookalike brand URLs.",
        "safe": "Hyphen count in the site name looks modest.",
    },
    "brand_impersonation_score": {
        "label": "Looks like a brand impersonation attempt",
        "risk": "Parts of the link resemble a known brand name in a deceptive way.",
        "safe": "Strong brand-impersonation signals were not detected.",
    },
}


@dataclass
class ExplanationResult:
    """SHAP explanation for a single URL prediction."""

    base_value: float
    shap_values: np.ndarray
    feature_names: list[str]
    feature_values: pd.Series
    top_positive: list[dict[str, Any]] = field(default_factory=list)
    top_negative: list[dict[str, Any]] = field(default_factory=list)
    plain_reasons_risk: list[str] = field(default_factory=list)
    plain_reasons_safe: list[str] = field(default_factory=list)
    advice: str = ""
    narrative: str = ""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def plain_label(feature: str) -> str:
    """Return a non-technical label for a feature name."""
    return FEATURE_GUIDE.get(feature, {}).get("label", feature.replace("_", " "))


def load_global_importance() -> list[dict[str, Any]]:
    """Load precomputed global feature importance."""
    path = _project_root() / "evaluation" / "shap" / "global_importance.json"
    if path.exists():
        rows = json.loads(path.read_text(encoding="utf-8"))
        for row in rows:
            row["plain_label"] = plain_label(row.get("feature", ""))
        return rows
    return []


def _enrich_contributions(
    pairs: list[tuple[str, float, Any]],
    *,
    positive: bool,
    limit: int = 6,
) -> list[dict[str, Any]]:
    """Attach plain-English metadata to top SHAP contributors."""
    selected = [p for p in pairs if (p[1] > 0 if positive else p[1] < 0)][:limit]
    enriched: list[dict[str, Any]] = []
    for name, shap_val, feat_val in selected:
        guide = FEATURE_GUIDE.get(name, {})
        enriched.append({
            "feature": name,
            "label": guide.get("label", name.replace("_", " ")),
            "shap": float(shap_val),
            "value": float(feat_val) if isinstance(feat_val, (int, float, np.floating)) else feat_val,
            "why": guide.get("risk" if positive else "safe", ""),
        })
    return enriched


def explain_url(url: str) -> ExplanationResult:
    """
    Compute local SHAP explanation for a URL.

    Args:
        url: Normalized URL string.

    Returns:
        ExplanationResult with SHAP values and narrative.
    """
    features = extract_features_dataframe([url])
    explainer = load_shap_explainer()
    shap_values = explainer.shap_values(features)

    if isinstance(shap_values, list):
        sv = np.asarray(shap_values[1])
        ev = explainer.expected_value
        base = float(ev[1] if isinstance(ev, (list, np.ndarray)) else ev)
    else:
        sv = np.asarray(shap_values)
        base = float(
            explainer.expected_value[1]
            if isinstance(explainer.expected_value, (list, np.ndarray))
            and len(np.asarray(explainer.expected_value).shape) > 0
            else explainer.expected_value
        )

    if sv.ndim == 3:
        sv = sv[0, :, 1]
    elif sv.ndim == 2:
        sv = sv[0]
    else:
        sv = sv.flatten()

    sv = sv.flatten()[: len(FEATURE_NAMES)]

    pairs = list(zip(FEATURE_NAMES, sv, features.iloc[0].values))
    pairs_sorted = sorted(pairs, key=lambda x: abs(x[1]), reverse=True)

    top_positive = _enrich_contributions(pairs_sorted, positive=True)
    top_negative = _enrich_contributions(pairs_sorted, positive=False)

    final_score = float(base + sv.sum())
    narrative, risk_reasons, safe_reasons, advice = generate_narrative(
        top_positive,
        top_negative,
        base,
        final_score,
    )

    return ExplanationResult(
        base_value=base,
        shap_values=sv,
        feature_names=FEATURE_NAMES,
        feature_values=features.iloc[0],
        top_positive=top_positive,
        top_negative=top_negative,
        plain_reasons_risk=risk_reasons,
        plain_reasons_safe=safe_reasons,
        advice=advice,
        narrative=narrative,
    )


def generate_narrative(
    top_positive: list[dict[str, Any]],
    top_negative: list[dict[str, Any]],
    base: float,
    final: float,
) -> tuple[str, list[str], list[str], str]:
    """
    Generate a non-technical explanation from SHAP contributions.

    Returns:
        narrative, risk_reasons, safe_reasons, advice
    """
    is_phishing = final > 0.5
    confidence_pct = int(round(max(final, 1.0 - final) * 100))

    risk_reasons = [
        item.get("why") or f"{item.get('label', item.get('feature'))} raised the risk score."
        for item in top_positive[:4]
        if item.get("why") or item.get("label")
    ]
    safe_reasons = [
        item.get("why") or f"{item.get('label', item.get('feature'))} lowered the risk score."
        for item in top_negative[:3]
        if item.get("why") or item.get("label")
    ]

    if is_phishing:
        headline = (
            f"**In plain English:** this link looks **risky**. "
            f"PhishLens thinks it is a **phishing** attempt "
            f"(about **{confidence_pct}%** confident)."
        )
        advice = (
            "Do **not** enter passwords, codes, or personal details on this page. "
            "If the link arrived by email or message, open the company's official website "
            "yourself instead of clicking through. When in doubt, ask IT or a trusted contact."
        )
        body = [
            headline,
            "",
            "**Why it looks suspicious**",
        ]
        body.extend(f"- {reason}" for reason in risk_reasons[:4])
        if safe_reasons:
            body.extend(["", "**What looked a bit safer**"])
            body.extend(f"- {reason}" for reason in safe_reasons[:2])
            body.append(
                "- Those safer signals were **not strong enough** to outweigh the warning signs."
            )
    else:
        headline = (
            f"**In plain English:** this link looks **safer**. "
            f"PhishLens thinks it is **legitimate** "
            f"(about **{confidence_pct}%** confident)."
        )
        advice = (
            "It still pays to stay alert: check the website name carefully, "
            "and avoid entering sensitive information unless you intended to visit this site. "
            "No automated check can guarantee absolute safety."
        )
        body = [
            headline,
            "",
            "**Why it looks safer**",
        ]
        body.extend(f"- {reason}" for reason in safe_reasons[:4])
        if risk_reasons:
            body.extend(["", "**Mild warning signs (not decisive)**"])
            body.extend(f"- {reason}" for reason in risk_reasons[:2])
            body.append("- These were present but did **not** dominate the final decision.")

    body.extend(["", f"**What you should do:** {advice}"])
    narrative = "\n".join(body)
    return narrative, risk_reasons, safe_reasons, advice


def plot_waterfall(explanation: ExplanationResult) -> plt.Figure:
    """Create SHAP waterfall plot for a single prediction."""
    order = np.argsort(-np.abs(explanation.shap_values))[:12]
    sv = explanation.shap_values[order]
    names = [plain_label(explanation.feature_names[i]) for i in order]
    data = explanation.feature_values.values[order]

    fig = plt.figure(figsize=(10, 6))
    shap.waterfall_plot(
        shap.Explanation(
            values=sv,
            base_values=explanation.base_value,
            data=data,
            feature_names=names,
        ),
        show=False,
        max_display=12,
    )
    plt.tight_layout()
    return fig


def plot_force_bar(explanation: ExplanationResult) -> plt.Figure:
    """Create a simplified force-plot style bar chart with plain labels."""
    pairs = sorted(
        zip(explanation.feature_names, explanation.shap_values),
        key=lambda x: abs(x[1]),
        reverse=True,
    )[:10]

    names = [plain_label(p[0]) for p in pairs]
    values = [p[1] for p in pairs]
    colors = ["#e85d5d" if v > 0 else "#5ec4d4" for v in values]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(names[::-1], values[::-1], color=colors[::-1])
    ax.axvline(0, color="white", linewidth=0.5, alpha=0.5)
    ax.set_xlabel("Impact on phishing risk (higher = more suspicious)")
    ax.set_title("What pushed this decision")
    fig.tight_layout()
    return fig
