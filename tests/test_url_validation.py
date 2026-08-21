"""Tests for URL validation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit_app.utils.url_validation import normalize_url, validate_url


def test_normalize_adds_scheme():
    assert normalize_url("google.com").startswith("https://")


def test_valid_url():
    result = validate_url("https://github.com/openai/triton")
    assert result.is_valid
    assert "github.com" in result.normalized_url


def test_empty_url_invalid():
    result = validate_url("")
    assert not result.is_valid


def test_malformed_url():
    result = validate_url("not a url at all !!!")
    assert not result.is_valid


def test_very_long_url_rejected():
    result = validate_url("https://example.com/" + "x" * 3000, max_length=2048)
    assert not result.is_valid
