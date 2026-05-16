# =========================================================
# app/services/recommendation.py
# =========================================================

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.config.settings import (
    FINAL_RECOMMENDATIONS,
    HIGH_CONFIDENCE_THRESHOLD,
    MIN_ACCEPTABLE_SCORE,
    TYPE_LIMITS,
)

from app.services.reranker import rerank_results

from app.services.validation_service import (
    validate_recommendations,
)

from app.utils.helpers import normalize

logger = logging.getLogger(__name__)

# =========================================================
# DOMAIN KEYWORDS
# =========================================================

FRONTEND_KEYWORDS = {
    "frontend",
    "javascript",
    "typescript",
    "react",
    "angular",
    "vue",
    "ui",
    "ux",
    "css",
    "html",
    "web",
}

BACKEND_KEYWORDS = {
    "backend",
    "java",
    "spring",
    "api",
    "microservices",
    "sql",
    "database",
    "python",
    "node",
    "server",
}

DATA_SCIENCE_KEYWORDS = {
    "data science",
    "data scientist",
    "machine learning",
    "deep learning",
    "ai",
    "analytics",
    "statistics",
    "python",
    "sql",
    "data analysis",
    "artificial intelligence",
    "reasoning",
    "predictive",
    "modeling",
}

COMMUNICATION_KEYWORDS = {
    "communication",
    "stakeholder",
    "presentation",
    "verbal",
    "interpersonal",
    "collaboration",
    "written",
    "facilitation",
}

LEADERSHIP_KEYWORDS = {
    "leadership",
    "management",
    "manager",
    "ownership",
    "strategic",
    "executive",
    "decision making",
    "people management",
}

COGNITIVE_KEYWORDS = {
    "cognitive",
    "reasoning",
    "problem solving",
    "critical thinking",
    "analytical",
    "logical",
    "aptitude",
}

SITUATIONAL_KEYWORDS = {
    "situational",
    "scenario",
    "judgement",
    "judgment",
    "customer service",
    "service",
    "simulation",
}

TECHNICAL_TEST_TYPES = {
    "K",
    "C",
}

# =========================================================
# HELPERS
# =========================================================


def contains_any(
    text: str,
    keywords: set[str],
) -> bool:

    normalized = normalize(text)

    return any(
        keyword in normalized
        for keyword in keywords
    )


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def build_searchable_text(
    item: dict[str, Any],
) -> str:

    return normalize(
        " ".join(
            [
                item.get("name", ""),
                item.get("description", ""),
                " ".join(
                    item.get(
                        "technical_skills",
                        [],
                    )
                ),
                " ".join(
                    item.get(
                        "communication_skills",
                        [],
                    )
                ),
                " ".join(
                    item.get(
                        "domains",
                        [],
                    )
                ),
                " ".join(
                    item.get(
                        "job_levels",
                        [],
                    )
                ),
            ]
        )
    )


# =========================================================
# QUERY INTENT
# =========================================================


def infer_query_intent(
    query: str,
) -> dict[str, bool]:

    normalized_query = normalize(query)

    intent = {
        "frontend": contains_any(
            normalized_query,
            FRONTEND_KEYWORDS,
        ),

        "backend": contains_any(
            normalized_query,
            BACKEND_KEYWORDS,
        ),

        "data_science": contains_any(
            normalized_query,
            DATA_SCIENCE_KEYWORDS,
        ),

        "communication": contains_any(
            normalized_query,
            COMMUNICATION_KEYWORDS,
        ),

        "leadership": contains_any(
            normalized_query,
            LEADERSHIP_KEYWORDS,
        ),

        "cognitive": contains_any(
            normalized_query,
            COGNITIVE_KEYWORDS,
        ),

        "situational": contains_any(
            normalized_query,
            SITUATIONAL_KEYWORDS,
        ),
    }

    logger.info(
        "Detected intent: %s",
        intent,
    )

    return intent


# =========================================================
# CONFIDENCE CALIBRATION
# =========================================================


def calibrate_confidence(
    score: float,
) -> float:

    score = max(
        min(score, 1.0),
        0.0,
    )

    if score >= 0.90:
        confidence = 0.96

    elif score >= 0.80:
        confidence = 0.92

    elif score >= 0.70:
        confidence = 0.88

    elif score >= 0.60:
        confidence = 0.82

    elif score >= 0.50:
        confidence = 0.74

    elif score >= 0.40:
        confidence = 0.66

    else:
        confidence = 0.55

    return round(confidence, 2)


# =========================================================
# RECOMMENDATION STRENGTH
# =========================================================


def infer_strength(
    confidence: float,
) -> str:

    if confidence >= HIGH_CONFIDENCE_THRESHOLD:
        return "high"

    if confidence >= 0.65:
        return "medium"

    return "low"


# =========================================================
# EXPLANATION GENERATION
# =========================================================


def build_explanation(
    item: dict[str, Any],
    intent: dict[str, bool],
) -> str:

    reasons: list[str] = []

    text = build_searchable_text(item)

    # =====================================================
    # FRONTEND
    # =====================================================

    if (
        intent["frontend"]
        and contains_any(
            text,
            FRONTEND_KEYWORDS,
        )
    ):
        reasons.append(
            "matches frontend engineering requirements"
        )

    # =====================================================
    # BACKEND
    # =====================================================

    if (
        intent["backend"]
        and contains_any(
            text,
            BACKEND_KEYWORDS,
        )
    ):
        reasons.append(
            "aligns with backend development and API skills"
        )

    # =====================================================
    # DATA SCIENCE
    # =====================================================

    if (
        intent["data_science"]
        and contains_any(
            text,
            DATA_SCIENCE_KEYWORDS,
        )
    ):
        reasons.append(
            "evaluates machine learning, analytics, and data science capabilities"
        )

    # =====================================================
    # COMMUNICATION
    # =====================================================

    if (
        intent["communication"]
        and contains_any(
            text,
            COMMUNICATION_KEYWORDS,
        )
    ):
        reasons.append(
            "evaluates communication and collaboration abilities"
        )

    # =====================================================
    # LEADERSHIP
    # =====================================================

    if (
        intent["leadership"]
        and contains_any(
            text,
            LEADERSHIP_KEYWORDS,
        )
    ):
        reasons.append(
            "supports leadership and stakeholder evaluation"
        )

    # =====================================================
    # COGNITIVE
    # =====================================================

    if intent["cognitive"]:

        test_type = item.get(
            "test_type",
            "",
        )

        if (
            test_type == "C"
            or contains_any(
                text,
                COGNITIVE_KEYWORDS,
            )
        ):
            reasons.append(
                "assesses cognitive reasoning and analytical problem-solving ability"
            )

    # =====================================================
    # SITUATIONAL
    # =====================================================

    if (
        intent["situational"]
        and contains_any(
            text,
            SITUATIONAL_KEYWORDS,
        )
    ):
        reasons.append(
            "measures situational judgement and customer interaction skills"
        )

    # =====================================================
    # DEFAULT FALLBACK
    # =====================================================

    if not reasons:

        test_type = item.get(
            "test_type",
            "K",
        )

        if test_type == "K":
            reasons.append(
                "assesses technical and job knowledge skills"
            )

        elif test_type == "C":
            reasons.append(
                "evaluates cognitive and analytical ability"
            )

        elif test_type == "P":
            reasons.append(
                "measures workplace personality traits"
            )

        elif test_type == "S":
            reasons.append(
                "assesses situational judgement and decision making"
            )

        elif test_type == "B":
            reasons.append(
                "evaluates behavioral competencies"
            )

        else:
            reasons.append(
                "matches the requested hiring criteria"
            )

    return (
        "This assessment "
        + ", ".join(reasons)
        + "."
    )


# =========================================================
# QUALITY FILTER
# =========================================================


def passes_quality_gate(
    item: dict[str, Any],
    intent: dict[str, bool],
) -> bool:

    score = safe_float(
        item.get("score", 0.0)
    )

    if score < MIN_ACCEPTABLE_SCORE:

        logger.info(
            "Rejected low-score result: %s (%s)",
            item.get("name"),
            score,
        )

        return False

    text = build_searchable_text(item)

    test_type = item.get(
        "test_type",
        "K",
    )

    # =====================================================
    # FRONTEND FILTER
    # =====================================================

    if intent["frontend"]:

        if (
            test_type in TECHNICAL_TEST_TYPES
            and not contains_any(
                text,
                FRONTEND_KEYWORDS,
            )
        ):

            logger.info(
                "Rejected frontend mismatch: %s",
                item.get("name"),
            )

            return False

    # =====================================================
    # BACKEND FILTER
    # =====================================================

    if intent["backend"]:

        if (
            test_type in TECHNICAL_TEST_TYPES
            and not contains_any(
                text,
                BACKEND_KEYWORDS,
            )
        ):

            logger.info(
                "Rejected backend mismatch: %s",
                item.get("name"),
            )

            return False

    # =====================================================
    # DATA SCIENCE FILTER
    # =====================================================

    if intent["data_science"]:

        if not contains_any(
            text,
            DATA_SCIENCE_KEYWORDS,
        ):

            logger.info(
                "Rejected data science mismatch: %s",
                item.get("name"),
            )

            return False

    # =====================================================
    # LEADERSHIP FILTER
    # =====================================================

    if intent["leadership"]:

        leadership_match = contains_any(
            text,
            LEADERSHIP_KEYWORDS,
        )

        if (
            not leadership_match
            and test_type not in {
                "P",
                "B",
                "S",
            }
        ):

            logger.info(
                "Rejected leadership mismatch: %s",
                item.get("name"),
            )

            return False

    # =====================================================
    # COGNITIVE FILTER
    # =====================================================

    if intent["cognitive"]:

        cognitive_match = contains_any(
            text,
            COGNITIVE_KEYWORDS,
        )

        if (
            test_type != "C"
            and not cognitive_match
        ):

            logger.info(
                "Rejected cognitive mismatch: %s",
                item.get("name"),
            )

            return False

    # =====================================================
    # SITUATIONAL FILTER
    # =====================================================

    if intent["situational"]:

        situational_match = contains_any(
            text,
            SITUATIONAL_KEYWORDS,
        )

        if (
            not situational_match
            and test_type != "S"
        ):

            logger.info(
                "Rejected situational mismatch: %s",
                item.get("name"),
            )

            return False

    return True


# =========================================================
# DIVERSITY ENFORCEMENT
# =========================================================


def enforce_diversity(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    final_results: list[
        dict[str, Any]
    ] = []

    type_counts = defaultdict(int)

    seen_names: set[str] = set()

    for item in results:

        name = item.get(
            "name",
            "",
        )

        if name in seen_names:
            continue

        seen_names.add(name)

        test_type = item.get(
            "test_type",
            "K",
        )

        limit = TYPE_LIMITS.get(
            test_type,
            FINAL_RECOMMENDATIONS,
        )

        if (
            type_counts[test_type]
            >= limit
        ):
            continue

        type_counts[test_type] += 1

        final_results.append(item)

        if (
            len(final_results)
            >= FINAL_RECOMMENDATIONS
        ):
            break

    return final_results


# =========================================================
# ENRICH RESULTS
# =========================================================


def enrich_result(
    item: dict[str, Any],
    intent: dict[str, bool],
) -> dict[str, Any]:

    enriched = dict(item)

    score = safe_float(
        enriched.get("score", 0.0)
    )

    confidence = calibrate_confidence(
        score
    )

    enriched["score"] = round(
        score,
        4,
    )

    enriched["confidence"] = confidence

    enriched[
        "high_confidence"
    ] = (
        confidence
        >= HIGH_CONFIDENCE_THRESHOLD
    )

    enriched[
        "recommendation_strength"
    ] = infer_strength(
        confidence
    )

    enriched[
        "explanation"
    ] = build_explanation(
        enriched,
        intent,
    )

    return enriched


# =========================================================
# MAIN PIPELINE
# =========================================================


def generate_recommendations(
    results: list[dict[str, Any]] | None = None,
    query: str = "",
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:

    try:

        results = results or []
        context = context or {}

        logger.info(
            "Incoming retrieval results: %s",
            len(results),
        )

        if not results:

            logger.warning(
                "No retrieval results received."
            )

            return []

        # =================================================
        # QUERY INTENT
        # =================================================

        intent = infer_query_intent(
            query
        )

        # =================================================
        # RERANK
        # =================================================

        ranked_results = rerank_results(
            results=results,
            query=query,
        )

        logger.info(
            "Reranker returned %s items",
            len(ranked_results),
        )

        if not ranked_results:

            logger.warning(
                "No reranked results generated."
            )

            return []

        # =================================================
        # FILTER
        # =================================================

        filtered_results = [
            item
            for item in ranked_results
            if passes_quality_gate(
                item,
                intent,
            )
        ]

        logger.info(
            "Filtered results count: %s",
            len(filtered_results),
        )

        # =================================================
        # FALLBACK
        # =================================================

        if not filtered_results:

            logger.warning(
                "Strict filtering removed all results. Using fallback recommendations."
            )

            filtered_results = ranked_results[
                :FINAL_RECOMMENDATIONS
            ]

        # =================================================
        # ENRICH
        # =================================================

        enriched_results = [
            enrich_result(
                item,
                intent,
            )
            for item in filtered_results
        ]

        logger.info(
            "Enriched results count: %s",
            len(enriched_results),
        )

        # =================================================
        # VALIDATE
        # =================================================

        validated_results = (
            validate_recommendations(
                enriched_results
            )
        )

        logger.info(
            "Validated results count: %s",
            len(validated_results),
        )

        # =================================================
        # VALIDATION FALLBACK
        # =================================================

        if not validated_results:

            logger.warning(
                "Validation removed all recommendations. Using safe fallback."
            )

            validated_results = enriched_results[
                :FINAL_RECOMMENDATIONS
            ]

        # =================================================
        # SORT
        # =================================================

        validated_results = sorted(
            validated_results,
            key=lambda x: safe_float(
                x.get("score", 0.0)
            ),
            reverse=True,
        )

        # =================================================
        # DIVERSITY
        # =================================================

        final_results = enforce_diversity(
            validated_results
        )

        logger.info(
            "Generated final recommendations: %s",
            len(final_results),
        )

        logger.info(
            "Final recommendation names: %s",
            [
                item.get("name")
                for item in final_results
            ],
        )

        return final_results

    except Exception as error:

        logger.exception(
            "Recommendation generation failed: %s",
            error,
        )

        return []