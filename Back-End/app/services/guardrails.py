import logging
import re

from app.utils.helpers import (
    normalize_text
)


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
# Only malicious intent phrases.
# Avoid blocking cybersecurity hiring queries.
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
    "terrorist attack"
]


# =========================================================
# OFFTOPIC PATTERNS
# Keep only clearly irrelevant topics.
# =========================================================

OFFTOPIC_PATTERNS = [

    "legal advice",
    "lawsuit",
    "court case",

    "medical diagnosis",
    "disease treatment",

    "politics",
    "election",

    "movie recommendation",
    "gaming pc",
    "travel itinerary"
]


# =========================================================
# SHL DOMAIN KEYWORDS
# =========================================================

SHL_SCOPE_KEYWORDS = [

    "assessment",
    "test",
    "candidate",
    "hiring",
    "recruitment",

    "personality",
    "technical",
    "cognitive",
    "behavioral",
    "communication",
    "leadership",

    "developer",
    "engineer",
    "manager",
    "analyst",
    "consultant",

    "java",
    "python",
    "cloud",
    "software",
    "coding",

    "opq",
    "gsa",
    "shl"
]


# =========================================================
# SAFE REGEX PATTERN CHECK
# =========================================================

def regex_contains_pattern(
    text,
    patterns
):
    """
    Exact normalized pattern match.
    """

    if not text:
        return False

    for pattern in patterns:

        escaped_pattern = re.escape(
            normalize_text(pattern)
        )

        if re.search(
            rf"\b{escaped_pattern}\b",
            text
        ):
            return True

    return False


# =========================================================
# DOMAIN CHECK
# =========================================================

def appears_in_scope(text):
    """
    Determines whether query
    appears related to SHL domain.
    """

    if not text:
        return False

    match_count = 0

    for keyword in SHL_SCOPE_KEYWORDS:

        escaped = re.escape(
            normalize_text(keyword)
        )

        if re.search(
            rf"\b{escaped}\b",
            text
        ):
            match_count += 1

    return match_count >= 1


# =========================================================
# MAIN SAFETY CHECK
# =========================================================

def is_safe_query(query):
    """
    Validates whether query is safe.
    """

    try:

        # =====================================
        # NULL / TYPE CHECK
        # =====================================

        if query is None:
            return False

        if not isinstance(
            query,
            str
        ):
            return False

        # =====================================
        # EMPTY QUERY
        # =====================================

        if query == "":
            return True

        # =====================================
        # UNICODE CLEANING
        # =====================================

        query = (
            query.encode(
                "utf-8",
                errors="ignore"
            )
            .decode("utf-8")
        )

        # =====================================
        # LENGTH CHECK
        # =====================================

        if len(query) > MAX_QUERY_LENGTH:

            logger.warning(
                "Blocked oversized query."
            )

            return False

        # =====================================
        # NORMALIZE
        # =====================================

        normalized_query = (
            normalize_text(query)
        )

        if not normalized_query:
            return False

        if (
            len(normalized_query)
            < MIN_QUERY_LENGTH
        ):
            return False

        # =====================================
        # BLOCKED SECURITY CHECK
        # =====================================

        if regex_contains_pattern(
            normalized_query,
            BLOCKED_PATTERNS
        ):

            logger.warning(
                "Blocked unsafe query."
            )

            return False

        # =====================================
        # OFFTOPIC CHECK
        # =====================================

        if regex_contains_pattern(
            normalized_query,
            OFFTOPIC_PATTERNS
        ):

            logger.warning(
                "Blocked off-topic query."
            )

            return False

        return True

    except Exception as error:

        logger.exception(
            f"Guardrail validation failed: "
            f"{error}"
        )

        return False


# =========================================================
# SHL DOMAIN VALIDATION
# =========================================================

def is_shl_related_query(query):
    """
    Determines whether query
    belongs to SHL domain.
    """

    try:

        if not query:
            return False

        normalized_query = (
            normalize_text(query)
        )

        return appears_in_scope(
            normalized_query
        )

    except Exception as error:

        logger.exception(
            f"SHL scope validation failed: "
            f"{error}"
        )

        return False


# =========================================================
# REFUSAL RESPONSE
# =========================================================

def refusal_response():

    return (
        "I can only assist with SHL "
        "assessment recommendations, "
        "assessment comparisons, "
        "and SHL-related hiring "
        "evaluation queries."
    )


# =========================================================
# OFFTOPIC RESPONSE
# =========================================================

def offtopic_response():

    return (
        "That request is outside "
        "the scope of SHL assessment "
        "recommendations. I can help "
        "with technical, personality, "
        "cognitive, leadership, and "
        "communication assessment "
        "selection."
    )