# =========================================================
# app/services/comparison.py
# Production-Grade Assessment Comparison Engine
# =========================================================

from __future__ import annotations

import logging
from typing import Any

from app.models.schemas import Recommendation

logger = logging.getLogger(__name__)

# =========================================================
# TEST TYPE LABELS
# =========================================================

TEST_TYPE_LABELS = {
    "K": "Knowledge",
    "P": "Personality",
    "A": "Cognitive Ability",
    "S": "Situational Judgement",
    "L": "Leadership",
}

# =========================================================
# SAFE ACCESS
# =========================================================


def safe_get(
    item: Any,
    field: str,
    default: Any = None,
) -> Any:

    # =====================================================
    # DICT
    # =====================================================

    if isinstance(item, dict):

        return item.get(
            field,
            default,
        )

    # =====================================================
    # PYDANTIC MODEL
    # =====================================================

    return getattr(
        item,
        field,
        default,
    )


# =========================================================
# SAFE STRING
# =========================================================


def safe_str(
    value: Any,
    fallback: str = "Not specified",
) -> str:

    if value is None:
        return fallback

    value = str(value).strip()

    if not value:
        return fallback

    return value


# =========================================================
# FORMAT ASSESSMENT
# =========================================================


def format_assessment(
    assessment: Recommendation | dict,
    index: int,
) -> str:

    name = safe_str(
        safe_get(
            assessment,
            "name",
        )
    )

    raw_test_type = safe_str(
        safe_get(
            assessment,
            "test_type",
            "K",
        )
    )

    test_type = TEST_TYPE_LABELS.get(
        raw_test_type,
        raw_test_type,
    )

    confidence = safe_get(
        assessment,
        "confidence",
        0,
    )

    strength = safe_str(
        safe_get(
            assessment,
            "recommendation_strength",
            "medium",
        )
    )

    description = safe_str(
        safe_get(
            assessment,
            "description",
        )
    )

    explanation = safe_str(
        safe_get(
            assessment,
            "explanation",
        )
    )

    try:

        confidence_percent = round(
            float(confidence) * 100,
            1,
        )

    except Exception:

        confidence_percent = 0.0

    return f"""
OPTION {index}

Assessment Name:
{name}

Assessment Type:
{test_type}

Confidence Score:
{confidence_percent}%

Recommendation Strength:
{strength.title()}

Description:
{description}

Why This Assessment Fits:
{explanation}
"""


# =========================================================
# BEST MATCH
# =========================================================


def determine_best_match(
    recommendations: list[
        Recommendation | dict
    ],
) -> Recommendation | dict | None:

    if not recommendations:
        return None

    sorted_items = sorted(
        recommendations,
        key=lambda x: (

            safe_get(
                x,
                "confidence",
                0,
            ),

            safe_get(
                x,
                "score",
                0,
            ),
        ),
        reverse=True,
    )

    return sorted_items[0]


# =========================================================
# MAIN COMPARISON
# =========================================================


def compare_assessments(
    recommendations: list[
        Recommendation | dict
    ],
) -> str:

    logger.info(
        "Running assessment comparison"
    )

    # =====================================================
    # EMPTY
    # =====================================================

    if not recommendations:

        return (
            "I could not find enough "
            "relevant SHL assessments "
            "to compare."
        )

    # =====================================================
    # SINGLE RESULT
    # =====================================================

    if len(recommendations) == 1:

        item = recommendations[0]

        return (
            f"I found one highly relevant "
            f"assessment recommendation:\n\n"
            f"{safe_get(item, 'name')}.\n\n"
            f"This assessment is currently "
            f"the strongest overall match "
            f"for the provided hiring "
            f"requirements."
        )

    # =====================================================
    # SORT RESULTS
    # =====================================================

    sorted_items = sorted(
        recommendations,
        key=lambda x: (

            safe_get(
                x,
                "confidence",
                0,
            ),

            safe_get(
                x,
                "score",
                0,
            ),
        ),
        reverse=True,
    )

    # =====================================================
    # BUILD RESPONSE
    # =====================================================

    sections: list[str] = []

    sections.append(
        "Here is a detailed comparison "
        "of the most relevant SHL "
        "assessments:\n"
    )

    for idx, item in enumerate(
        sorted_items,
        start=1,
    ):

        sections.append(
            "=================================================="
        )

        sections.append(
            format_assessment(
                item,
                idx,
            )
        )

    # =====================================================
    # BEST MATCH
    # =====================================================

    best = determine_best_match(
        sorted_items
    )

    if best:

        sections.append(
            "=================================================="
        )

        sections.append(
            "BEST OVERALL RECOMMENDATION"
        )

        sections.append(
            "=================================================="
        )

        sections.append(
            f"{safe_get(best, 'name')} "
            f"is the strongest overall "
            f"recommendation based on "
            f"confidence score, role alignment, "
            f"and competency relevance."
        )

    return "\n".join(sections)