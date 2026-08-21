"""Lexical and host-based URL feature extraction for phishing detection."""

from __future__ import annotations

import math
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd
import tldextract

from streamlit_app.utils.url_validation import normalize_url

# Suspicious tokens commonly found in phishing URLs
SUSPICIOUS_KEYWORDS = (
    "login", "verify", "secure", "account", "update", "confirm", "wallet",
    "reset", "bank", "paypal", "signin", "webscr", "password", "credential",
    "suspend", "alert", "free", "bonus", "gift", "microsft", "microsoft",
    "apple", "amazon", "support", "validation", "unlock", "billing",
)

# TLDs frequently abused in phishing campaigns
SUSPICIOUS_TLDS = {
    "zip", "mov", "xyz", "top", "click", "country", "support", "loan",
    "tk", "ml", "cf", "ga", "gq", "work", "buzz", "cam", "rest",
}

FEATURE_NAMES: list[str] = [
    "url_length",
    "hostname_length",
    "path_length",
    "query_length",
    "num_dots",
    "num_hyphens",
    "num_underscores",
    "num_slashes",
    "num_digits",
    "num_special_chars",
    "subdomain_count",
    "path_depth",
    "query_param_count",
    "has_https",
    "has_http",
    "has_at_symbol",
    "has_ip_host",
    "has_port",
    "has_double_slash_redirect",
    "suspicious_keyword_count",
    "has_suspicious_keyword",
    "is_suspicious_tld",
    "tld_length",
    "digit_ratio_hostname",
    "letter_ratio_hostname",
    "hostname_entropy",
    "path_entropy",
    "url_entropy",
    "long_url",
    "very_long_url",
    "short_hostname",
    "many_subdomains",
    "many_hyphens",
    "brand_impersonation_score",
]


def _shannon_entropy(text: str) -> float:
    """Compute Shannon entropy of a string."""
    if not text:
        return 0.0
    freq: dict[str, int] = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(text)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


def _count_special_chars(text: str) -> int:
    """Count non-alphanumeric characters excluding common URL separators."""
    return sum(1 for c in text if not c.isalnum() and c not in ".-_/:?=&%#")


def _brand_impersonation_score(url_lower: str) -> float:
    """Heuristic score for brand-impersonation tokens in URL."""
    brands = ("paypal", "microsoft", "apple", "google", "amazon", "facebook", "netflix")
    score = 0.0
    for brand in brands:
        if brand in url_lower and brand not in url_lower.split("/")[2]:
            # brand appears but not as exact domain
            score += 1.0
    return score


def extract_features_from_url(raw_url: str) -> dict[str, Any]:
    """
    Extract lexical and host-based features from a single URL.

    Args:
        raw_url: Raw or normalized URL string.

    Returns:
        Dictionary mapping feature names to numeric values.
    """
    normalized = normalize_url(raw_url)
    parsed = urlparse(normalized)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""
    full_lower = normalized.lower()

    extracted = tldextract.extract(normalized)
    subdomain = extracted.subdomain or ""
    subdomain_count = len([s for s in subdomain.split(".") if s]) if subdomain else 0

    suspicious_kw_count = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in full_lower)
    tld = (extracted.suffix or "").lower()

    ip_pattern = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
    has_ip = bool(hostname and ip_pattern.match(hostname))

    hostname_alpha = sum(c.isalpha() for c in hostname)
    hostname_digits = sum(c.isdigit() for c in hostname)
    hostname_len = max(len(hostname), 1)

    features = {
        "url_length": len(normalized),
        "hostname_length": len(hostname),
        "path_length": len(path),
        "query_length": len(query),
        "num_dots": normalized.count("."),
        "num_hyphens": normalized.count("-"),
        "num_underscores": normalized.count("_"),
        "num_slashes": normalized.count("/"),
        "num_digits": sum(c.isdigit() for c in normalized),
        "num_special_chars": _count_special_chars(normalized),
        "subdomain_count": subdomain_count,
        "path_depth": len([p for p in path.split("/") if p]),
        "query_param_count": len(parse_qs(query)),
        "has_https": 1 if parsed.scheme == "https" else 0,
        "has_http": 1 if parsed.scheme == "http" else 0,
        "has_at_symbol": 1 if "@" in normalized else 0,
        "has_ip_host": 1 if has_ip else 0,
        "has_port": 1 if parsed.port is not None else 0,
        "has_double_slash_redirect": 1 if "//" in path else 0,
        "suspicious_keyword_count": suspicious_kw_count,
        "has_suspicious_keyword": 1 if suspicious_kw_count > 0 else 0,
        "is_suspicious_tld": 1 if tld in SUSPICIOUS_TLDS else 0,
        "tld_length": len(tld),
        "digit_ratio_hostname": hostname_digits / hostname_len,
        "letter_ratio_hostname": hostname_alpha / hostname_len,
        "hostname_entropy": _shannon_entropy(hostname),
        "path_entropy": _shannon_entropy(path),
        "url_entropy": _shannon_entropy(normalized),
        "long_url": 1 if len(normalized) > 60 else 0,
        "very_long_url": 1 if len(normalized) > 100 else 0,
        "short_hostname": 1 if len(hostname) < 5 else 0,
        "many_subdomains": 1 if subdomain_count >= 3 else 0,
        "many_hyphens": 1 if hostname.count("-") >= 2 else 0,
        "brand_impersonation_score": _brand_impersonation_score(full_lower),
    }
    return features


def extract_features_dataframe(urls: list[str]) -> pd.DataFrame:
    """Extract features for multiple URLs into a DataFrame."""
    rows = [extract_features_from_url(url) for url in urls]
    df = pd.DataFrame(rows, columns=FEATURE_NAMES)
    return df.fillna(0.0)


def get_parsed_url_details(raw_url: str) -> dict[str, Any]:
    """Return human-readable URL anatomy for the dashboard."""
    normalized = normalize_url(raw_url)
    parsed = urlparse(normalized)
    extracted = tldextract.extract(normalized)
    hostname = parsed.hostname or ""
    return {
        "hostname": hostname,
        "tld": extracted.suffix or "",
        "scheme": (parsed.scheme or "http").upper(),
        "path_depth": len([p for p in (parsed.path or "").split("/") if p]),
        "query_params": len(parse_qs(parsed.query or "")),
        "length": len(normalized),
        "has_ip": bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname)),
        "has_at": "@" in normalized,
        "hyphens": hostname.count("-"),
        "digits": sum(c.isdigit() for c in hostname),
        "subdomains": len([s for s in (extracted.subdomain or "").split(".") if s]),
    }
