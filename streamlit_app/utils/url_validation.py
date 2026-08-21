"""URL validation utilities for PhishLens."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import validators


@dataclass
class URLValidationResult:
    """Outcome of URL validation."""

    is_valid: bool
    normalized_url: str
    error: Optional[str] = None


def normalize_url(raw: str) -> str:
    """Normalize a URL string for parsing and feature extraction."""
    cleaned = raw.strip()
    if not cleaned:
        return ""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", cleaned):
        cleaned = f"https://{cleaned}"
    return cleaned


def validate_url(raw: str, max_length: int = 2048) -> URLValidationResult:
    """
    Validate and normalize a user-supplied URL.

    Args:
        raw: Raw URL input.
        max_length: Maximum allowed URL length.

    Returns:
        URLValidationResult with normalized URL or error message.
    """
    if not raw or not raw.strip():
        return URLValidationResult(False, "", "URL cannot be empty.")

    if len(raw) > max_length:
        return URLValidationResult(
            False,
            "",
            f"URL exceeds maximum length of {max_length} characters.",
        )

    normalized = normalize_url(raw)
    parsed = urlparse(normalized)

    if not parsed.netloc:
        return URLValidationResult(False, "", "URL must contain a valid hostname.")

    if not validators.url(normalized):
        return URLValidationResult(False, "", "URL format is invalid.")

    hostname = parsed.hostname or ""
    if not hostname or len(hostname) > 253:
        return URLValidationResult(False, "", "Hostname is invalid or too long.")

    return URLValidationResult(True, normalized)
