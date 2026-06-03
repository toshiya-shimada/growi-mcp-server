from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {"access_token", "growi_access_token", "authorization"}


def redact_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of the mapping with sensitive values replaced by ***REDACTED***."""

    redacted: dict[str, Any] = {}
    for key, value in mapping.items():
        if key.lower() in SENSITIVE_KEYS and value:
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value
    return redacted
