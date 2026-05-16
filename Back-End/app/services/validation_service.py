# =========================================================
# app/services/validation_service.py
# =========================================================

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from app.config.settings import (
    FINAL_RECOMMENDATIONS,
    REMOVE_DUPLICATES,
    REQUIRE_SHL_DOMAIN,
    STRICT_URL_VALIDATION,
    VALID_TEST_TYPES,
)

from app.utils.helpers import normalize

logger = logging.getLogger(__name__)

# =========================================================
# CONSTANTS
# =========================================================

REQUIRED_FIELDS = {
    "name",
    "url",
}

VALID_MESSAGE_ROLES = {
    "user",
    "assistant",
    "system",
}

ALLOWED_DOMAINS = {
    "shl.com",
    "www.shl.com",
}

MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 200

# =========================================================
# TEST TYPE NORMALIZATION
# ONLY VALID TYPES ALLOWED
# =========================================================

VALID_TEST_TYPE_MAPPINGS = {
    "knowledge": "K",
    "technical": "K",
    "coding": "K",

    "personality": "P",
    "behavioral": "P",
    "opq": "P",

    "cognitive": "A",
    "ability": "A",
    "reasoning": "A",

    "situational": "S",
    "judgement": "S",
    "scenario": "S",

    "communication": "B",
    "leadership": "B",

    "k": "K",
    "p": "P",
    "a": "A",
    "s": "S",
    "b": "B",
}

# =========================================================
# URL VALIDATION
# =========================================================

def is_valid_url(url: str) -> bool:

    if not url or not isinstance(url, str):
        return False

    try:

        parsed = urlparse(url.strip())

        if STRICT_URL_VALIDATION:

            if parsed.scheme not in {
                "http",
                "https",
            }:
                return False

        if REQUIRE_SHL_DOMAIN:

            domain = parsed.netloc.lower()

            if not any(
                allowed in domain
                for allowed in ALLOWED_DOMAINS
            ):
                return False

        return True

    except Exception as error:

        logger.warning(
            "URL validation failed: %s",
            error,
        )

        return False

# =========================================================
# TEST TYPE NORMALIZATION
# =========================================================

def normalize_test_type(
    value: str | None,
) -> str:

    if not value:
        return "K"

    normalized = normalize(value)

    mapped = VALID_TEST_TYPE_MAPPINGS.get(
        normalized,
        "K",
    )

    if mapped not in VALID_TEST_TYPES:
        return "K"

    return mapped

# =========================================================
# SCORE NORMALIZATION
# =========================================================

def normalize_score(
    value: Any,
) -> float:

    try:

        score = float(value)

        return max(
            0.0,
            min(score, 1.0),
        )

    except Exception:
        return 0.0

# =========================================================
# SANITIZATION
# =========================================================

def sanitize_recommendation(
    item: dict[str, Any],
) -> dict[str, Any]:

    cleaned = dict(item)

    cleaned["name"] = str(
        cleaned.get("name", "")
    ).strip()

    cleaned["url"] = str(
        cleaned.get("url", "")
    ).strip()

    cleaned["description"] = str(
        cleaned.get("description", "")
    ).strip()

    cleaned["test_type"] = normalize_test_type(
        cleaned.get("test_type")
    )

    cleaned["score"] = normalize_score(
        cleaned.get("score", 0.0)
    )

    return cleaned

# =========================================================
# QUALITY VALIDATION
# =========================================================

def is_quality_recommendation(
    item: dict[str, Any],
) -> bool:

    name = normalize(
        item.get("name", "")
    )

    if not name:
        return False

    if len(name) < MIN_NAME_LENGTH:
        return False

    if len(name) > MAX_NAME_LENGTH:
        return False

    banned = {
        "unknown",
        "n/a",
        "null",
    }

    if name in banned:
        return False

    return True

# =========================================================
# RESULT VALIDATION
# =========================================================

def validate_result(
    item: dict[str, Any],
) -> tuple[bool, str]:

    if not isinstance(item, dict):
        return False, "not_dict"

    # REQUIRED FIELDS

    for field in REQUIRED_FIELDS:

        value = item.get(field)

        if not value:
            return False, f"missing_{field}"

    # NAME

    name = normalize(
        item.get("name", "")
    )

    if len(name) < MIN_NAME_LENGTH:
        return False, "invalid_name"

    # URL

    if not is_valid_url(
        item.get("url")
    ):
        return False, "invalid_url"

    # TEST TYPE

    test_type = item.get(
        "test_type",
        "K",
    )

    if test_type not in VALID_TEST_TYPES:
        return False, "invalid_test_type"

    # QUALITY

    if not is_quality_recommendation(
        item
    ):
        return False, "low_quality"

    return True, "valid"

# =========================================================
# DEDUPLICATION
# =========================================================

def remove_duplicates(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    unique = []
    seen = set()

    for item in results:

        key = (
            normalize(
                item.get("name", "")
            ),
            normalize(
                item.get("url", "")
            ),
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(item)

    return unique

# =========================================================
# SORTING
# =========================================================

def sort_results(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    return sorted(
        results,
        key=lambda item: (
            item.get("score", 0.0),
            normalize(
                item.get("name", "")
            ),
        ),
        reverse=True,
    )

# =========================================================
# VALIDATION PIPELINE
# =========================================================

def validate_recommendations(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    if not results:

        logger.warning(
            "No recommendations received"
        )

        return []

    validated = []

    for item in results:

        try:

            # HANDLE STRING RESULTS
            # IMPORTANT FIX

            if isinstance(item, str):

                logger.warning(
                    "Skipping string recommendation: %s",
                    item,
                )

                continue

            cleaned = sanitize_recommendation(
                item
            )

            is_valid, reason = validate_result(
                cleaned
            )

            if is_valid:

                validated.append(cleaned)

            else:

                logger.warning(
                    "Rejected recommendation '%s': %s",
                    cleaned.get("name"),
                    reason,
                )

        except Exception as error:

            logger.exception(
                "Validation failure: %s",
                error,
            )

    if REMOVE_DUPLICATES:

        validated = remove_duplicates(
            validated
        )

    validated = sort_results(
        validated
    )

    validated = validated[
        :FINAL_RECOMMENDATIONS
    ]

    logger.info(
        "Validated recommendations: %s",
        len(validated),
    )

    return validated

# =========================================================
# RESPONSE SCHEMA VALIDATION
# =========================================================

def validate_response_schema(
    payload: dict[str, Any],
) -> bool:

    if not isinstance(payload, dict):
        return False

    required_fields = {
        "reply",
        "recommendations",
        "end_of_conversation",
    }

    if not required_fields.issubset(
        payload.keys()
    ):
        return False

    if not isinstance(
        payload["reply"],
        str,
    ):
        return False

    if not isinstance(
        payload["recommendations"],
        list,
    ):
        return False

    if not isinstance(
        payload["end_of_conversation"],
        bool,
    ):
        return False

    return True

# =========================================================
# MESSAGE VALIDATION
# =========================================================

def validate_single_message(
    message: dict[str, Any],
) -> bool:

    if not isinstance(message, dict):
        return False

    role = message.get("role")
    content = message.get("content")

    if role not in VALID_MESSAGE_ROLES:
        return False

    if not isinstance(content, str):
        return False

    if not content.strip():
        return False

    return True

def validate_messages(
    messages: list[dict[str, Any]],
) -> bool:

    if not isinstance(messages, list):
        return False

    if not messages:
        return False

    return all(
        validate_single_message(message)
        for message in messages
    )