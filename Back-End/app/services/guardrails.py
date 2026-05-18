# =========================================================
# app/services/guardrails.py
# Production-Grade Guardrails Engine
# FULLY FIXED VERSION
# =========================================================

from __future__ import annotations

import logging
import re
from typing import Iterable

from app.utils.helpers import normalize_text

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(__name__)

# =========================================================
# LIMITS
# =========================================================

MAX_QUERY_LENGTH = 2000
MIN_QUERY_LENGTH = 2

# =========================================================
# BLOCKED SECURITY PATTERNS
# =========================================================

BLOCKED_PATTERNS = [

    # =====================================
    # Prompt Injection
    # =====================================

    "ignore previous instructions",
    "ignore all instructions",
    "reveal system prompt",
    "show hidden prompt",
    "developer message",
    "system prompt",
    "jailbreak",
    "prompt injection",

    # =====================================
    # Cyber Abuse
    # =====================================

    "how to hack",
    "hack into",
    "build malware",
    "create malware",
    "deploy malware",
    "write ransomware",
    "create ransomware",
    "launch ddos",
    "perform ddos",
    "reverse shell payload",
    "steal credentials",
    "phishing attack",

    # =====================================
    # SQL Injection / XSS
    # =====================================

    "<script>",
    "drop table",
    "union select",
    "or 1=1",

    # =====================================
    # Illegal / Dangerous
    # =====================================

    "illegal activity",
    "bypass law",
    "commit fraud",
    "build bomb",
    "terrorist attack",
]

# =========================================================
# HARD OFFTOPIC PATTERNS
# =========================================================

OFFTOPIC_PATTERNS = [

    # Food
    "biriyani",
    "biryani",
    "pizza",
    "burger",
    "recipe",

    # Entertainment
    "movie",
    "cinema",
    "song",
    "music",

    # Travel
    "travel",
    "trip",
    "tourism",

    # Finance
    "crypto",
    "bitcoin",
    "investment",
    "stock market",

    # Politics
    "politics",
    "election",

    # Medical
    "medical diagnosis",
    "disease treatment",

    # Shopping
    "iphone",
    "laptop price",

    # Misc
    "gaming",
    "pubg",
    "instagram",
    "whatsapp",
]

# =========================================================
# SHL DOMAIN KEYWORDS
# =========================================================

SHL_SCOPE_KEYWORDS = [

    # Core SHL
    "shl",
    "assessment",
    "assessment recommendation",
    "assessment test",
    "assessment solution",
    "assessment selection",

    # Hiring
    "hiring",
    "recruitment",
    "candidate",
    "interview",
    "job role",
    "job assessment",

    # Test Categories
    "technical",
    "coding",
    "cognitive",
    "behavioral",
    "behavioural",
    "personality",
    "leadership",
    "communication",
    "aptitude",
    "situational",

    # Roles
    "developer",
    "engineer",
    "manager",
    "analyst",
    "architect",
    "consultant",
    "scientist",

    # Technologies
    "python",
    "java",
    "javascript",
    "react",
    "angular",
    "sql",
    "aws",
    "cloud",
    "docker",
    "kubernetes",
    "devops",
    "backend",
    "frontend",
    "full stack",

    # SHL Products
    "opq",
    "gsa",
]

# =========================================================
# MINIMUM VALID DOMAIN TERMS
# =========================================================

VALID_DOMAIN_TERMS = {

    "assessment",
    "test",
    "candidate",
    "hiring",
    "recruitment",
    "technical",
    "coding",
    "behavioral",
    "behavioural",
    "personality",
    "leadership",
    "communication",
    "cognitive",
    "aptitude",
    "developer",
    "engineer",
    "manager",
    "analyst",
    "python",
    "java",
    "react",
    "sql",
    "cloud",
    "docker",
    "aws",
    "backend",
    "frontend",
    "devops",
    "shl",
}

# =========================================================
# SAFE REGEX CHECK
# =========================================================

def regex_contains_pattern(
    text: str,
    patterns: Iterable[str],
) -> bool:
    """
    Safe normalized whole-word pattern matching.
    """

    if not text:
        return False

    for pattern in patterns:

        normalized_pattern = normalize_text(pattern)

        escaped = re.escape(
            normalized_pattern
        )

        if re.search(
            rf"\b{escaped}\b",
            text,
            flags=re.IGNORECASE,
        ):
            return True

    return False

# =========================================================
# TOKENIZER
# =========================================================

def tokenize(text: str) -> list[str]:
    """
    Lightweight tokenizer.
    """

    if not text:
        return []

    return re.findall(
        r"[a-zA-Z0-9\+\#\.]+",
        text.lower(),
    )

# =========================================================
# DOMAIN VALIDATION
# =========================================================

def appears_in_scope(
    text: str,
) -> bool:
    """
    Strict SHL domain validation.
    Prevents random/offtopic queries
    from reaching retrieval pipeline.
    """

    if not text:
        return False

    text = normalize_text(text)

    # =====================================================
    # DIRECT KEYWORD MATCH
    # =====================================================

    keyword_matches = 0

    for keyword in SHL_SCOPE_KEYWORDS:

        escaped = re.escape(
            normalize_text(keyword)
        )

        if re.search(
            rf"\b{escaped}\b",
            text,
            flags=re.IGNORECASE,
        ):
            keyword_matches += 1

    if keyword_matches >= 1:
        return True

    # =====================================================
    # TOKEN VALIDATION
    # =====================================================

    tokens = tokenize(text)

    valid_matches = sum(
        1
        for token in tokens
        if token in VALID_DOMAIN_TERMS
    )

    return valid_matches >= 1

# =========================================================
# MAIN SAFETY CHECK
# =========================================================

def is_safe_query(
    query: str,
) -> bool:
    """
    Main validation entrypoint.
    """

    try:

        # =====================================
        # NULL / TYPE CHECK
        # =====================================

        if query is None:
            return False

        if not isinstance(
            query,
            str,
        ):
            return False

        # =====================================
        # CLEAN UTF
        # =====================================

        query = (
            query.encode(
                "utf-8",
                errors="ignore",
            )
            .decode("utf-8")
        )

        # =====================================
        # NORMALIZE
        # =====================================

        normalized_query = normalize_text(
            query
        )

        if not normalized_query:
            return False

        # =====================================
        # LENGTH CHECK
        # =====================================

        if (
            len(normalized_query)
            > MAX_QUERY_LENGTH
        ):

            logger.warning(
                "Blocked oversized query."
            )

            return False

        if (
            len(normalized_query)
            < MIN_QUERY_LENGTH
        ):

            logger.warning(
                "Blocked short query."
            )

            return False

        # =====================================
        # SECURITY CHECK
        # =====================================

        if regex_contains_pattern(
            normalized_query,
            BLOCKED_PATTERNS,
        ):

            logger.warning(
                "Blocked malicious query."
            )

            return False

        # =====================================
        # OFFTOPIC CHECK
        # =====================================

        if regex_contains_pattern(
            normalized_query,
            OFFTOPIC_PATTERNS,
        ):

            logger.warning(
                "Blocked off-topic query."
            )

            return False

        return True

    except Exception as error:

        logger.exception(
            "Guardrail validation failed: %s",
            error,
        )

        return False

# =========================================================
# SHL DOMAIN VALIDATION
# =========================================================

def is_shl_related_query(
    query: str,
) -> bool:
    """
    Determines whether query belongs
    to SHL assessment recommendation domain.
    """

    try:

        if not query:
            return False

        normalized_query = normalize_text(
            query
        )

        if not normalized_query:
            return False

        # =====================================================
        # BLOCK OBVIOUS OFFTOPIC
        # =====================================================

        if regex_contains_pattern(
            normalized_query,
            OFFTOPIC_PATTERNS,
        ):
            return False

        return appears_in_scope(
            normalized_query
        )

    except Exception as error:

        logger.exception(
            "SHL scope validation failed: %s",
            error,
        )

        return False

# =========================================================
# REFUSAL RESPONSE
# =========================================================

def refusal_response() -> str:

    return (
        "I can only assist with SHL assessment "
        "recommendations, hiring evaluations, "
        "candidate assessment selection, "
        "assessment comparisons, and recruitment-related queries."
    )

# =========================================================
# OFFTOPIC RESPONSE
# =========================================================

def offtopic_response() -> str:

    return (
        "Please ask a SHL assessment-related query. "
        "Example: 'Java developer technical assessment', "
        "'leadership assessment for managers', "
        "or 'compare cognitive and personality tests'."
    )