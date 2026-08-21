"""Tests for URL feature extraction."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit_app.utils.feature_extraction import (
    FEATURE_NAMES,
    extract_features_dataframe,
    extract_features_from_url,
)


def test_feature_count():
    features = extract_features_from_url("https://www.google.com")
    assert len(features) == len(FEATURE_NAMES)


def test_phishing_url_has_suspicious_features():
    url = "http://secure-login-microsft.com/verify?id=983"
    features = extract_features_from_url(url)
    assert features["has_suspicious_keyword"] == 1
    assert features["url_length"] > 30


def test_https_legitimate_url():
    features = extract_features_from_url("https://github.com/openai/triton")
    assert features["has_https"] == 1
    assert features["has_ip_host"] == 0


def test_ip_host_detection():
    features = extract_features_from_url("http://192.168.1.1/login")
    assert features["has_ip_host"] == 1


def test_dataframe_shape():
    urls = ["https://google.com", "http://evil-phish.xyz/login"]
    df = extract_features_dataframe(urls)
    assert df.shape == (2, len(FEATURE_NAMES))


def test_very_long_url():
    long_url = "https://example.com/" + "a" * 500
    features = extract_features_from_url(long_url)
    assert features["very_long_url"] == 1
