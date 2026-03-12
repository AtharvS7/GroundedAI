"""Prompt injection detection middleware.

Scans incoming queries for known injection patterns and blocks them.
"""

from __future__ import annotations

import logging
import re
from typing import List

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+all\s+instructions",
    r"you\s+are\s+now",
    r"new\s+persona",
    r"system\s+prompt",
    r"disregard",
    r"jailbreak",
    r"dan\s+mode",
    r"pretend\s+you\s+are",
    r"override\s+(your|all)\s+instructions",
    r"forget\s+(your|all|everything)",
]

_compiled_patterns = [
    re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS
]


def check_injection(text: str) -> bool:
    """Check if the text contains prompt injection patterns.

    Args:
        text: Input text to check.

    Returns:
        True if injection pattern detected, False otherwise.
    """
    for pattern in _compiled_patterns:
        if pattern.search(text):
            return True
    return False


def validate_query_text(query: str) -> None:
    """Validate query text for injection attempts.

    Raises:
        HTTPException: 400 if injection detected.
    """
    if check_injection(query):
        logger.warning(f"Prompt injection attempt blocked: {query[:100]}...")
        raise HTTPException(
            status_code=400,
            detail="Your query was blocked due to suspected prompt injection. "
            "Please rephrase your question.",
        )
