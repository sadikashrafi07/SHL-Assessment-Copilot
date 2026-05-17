# =========================================================
# app/services/recommendation.py
# Production Recommendation Engine
# Enterprise Hybrid Recommendation Layer
# FULLY FIXED VERSION
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
    "front end",
    "javascript",
    "typescript",
    "react",
    "reactjs",
    "angular",
    "vue",
    "vuejs",
    "ui",
    "ux",
    "css",
    "html",
    "web",
    "accessibility",
    "responsive",
}

BACKEND_KEYWORDS = {
    "backend",
    "back end",
    "java",
    "spring",
    "api",
    "microservices",
    "sql",
    "database",
    "python",
    "node",
    "server",
    "django",
    "flask",
    "fastapi",
    "rest",
}

DATA_SCIENCE_KEYWORDS = {
    "data science",
    "data scientist",
    "machine learning",
    "deep learning",
    "analytics",
    "statistics",
    "statistical",
    "ai",
    "artificial intelligence",
    "nlp",
    "predictive",
    "modeling",
    "classification",
    "regression",
    "neural network",
    "pandas",
    "numpy",
}

COMMUNICATION_KEYWORDS = {
    "business communication",
    "interpersonal communication",
    "communication",
    "presentation",
    "stakeholder",
    "written communication",
    "verbal communication",
    "collaboration",
    "negotiation",
    "listening",
    "facilitation",
}

LEADERSHIP_KEYWORDS = {
    "leadership",
    "leader",
    "management",
    "manager",
    "stakeholder management",
    "people management",
    "executive",
    "strategic",
    "ownership",
    "decision making",
    "organizational",
}

COGNITIVE_KEYWORDS = {
    "cognitive",
    "reasoning",
    "logical",
    "analytical",
    "problem solving",
    "critical thinking",
    "numerical",
    "deductive",
    "inductive",
}

SITUATIONAL_KEYWORDS = {
    "situational",
    "judgement",
    "judgment",
    "scenario",
    "simulation",
    "decision making",
}

# =========================================================
# NEGATIVE KEYWORDS
# Prevent False Positives
# =========================================================

IRRELEVANT_COMMUNICATION_CONTEXT = {
    "telecommunication",
    "telecommunications",
    "microwave",
    "signal processing",
    "electromagnetism",
    "network engineering",
    "instrumentation",
    "semiconductor",
    "electronics",
}

# =========================================================
# TEST TYPE PRIORITY
# =========================================================

TEST_TYPE_WEIGHTS = {
    "K": 1.12,
    "A": 1.08,
    "S": 1.04,
    "L": 1.10,
    "P": 1.02,
}

# =========================================================
# HELPERS
# =========================================================


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def contains_any(
    text: str,
    keywords: set[str],
) -> bool:

    normalized = normalize(text)

    return any(
        keyword in normalized
        for keyword in keywords
    )


def build_searchable_text(
    item: dict[str, Any],
) -> str:

    values: list[str] = []

    string_fields = [
        "name",
        "description",
    ]

    list_fields = [
        "domains",
        "roles",
        "job_levels",
        "technical_skills",
        "communication_skills",
        "leadership_traits",
        "expanded_competencies",
        "matched_domains",
        "matched_roles",
        "matched_competencies",
    ]

    for field in string_fields:

        value = item.get(field)

        if value:
            values.append(str(value))

    for field in list_fields:

        field_values = item.get(field, [])

        if isinstance(field_values, list):

            values.extend(
                str(v)
                for v in field_values
                if v
            )

    return normalize(
        " ".join(values)
    )


# =========================================================
# QUERY INTENT
# =========================================================


def infer_query_intent(
    query: str,
) -> dict[str, bool]:

    query = normalize(query)

    intent = {
        "frontend": contains_any(
            query,
            FRONTEND_KEYWORDS,
        ),

        "backend": contains_any(
            query,
            BACKEND_KEYWORDS,
        ),

        "data_science": contains_any(
            query,
            DATA_SCIENCE_KEYWORDS,
        ),

        "communication": contains_any(
            query,
            COMMUNICATION_KEYWORDS,
        ),

        "leadership": contains_any(
            query,
            LEADERSHIP_KEYWORDS,
        ),

        "cognitive": contains_any(
            query,
            COGNITIVE_KEYWORDS,
        ),

        "situational": contains_any(
            query,
            SITUATIONAL_KEYWORDS,
        ),
    }

    logger.info(
        "Detected query intent: %s",
        intent,
    )

    return intent


# =========================================================
# CONFIDENCE
# =========================================================


def calibrate_confidence(
    score: float,
) -> float:

    score = max(
        min(score, 1.0),
        0.0,
    )

    confidence = (
        0.45 + (score * 0.50)
    )

    return round(
        min(confidence, 0.99),
        2,
    )


# =========================================================
# STRENGTH
# =========================================================


def infer_strength(
    confidence: float,
) -> str:

    if confidence >= 0.85:
        return "high"

    if confidence >= 0.70:
        return "medium"

    return "low"


# =========================================================
# EXPLANATION
# =========================================================


def build_explanation(
    item: dict[str, Any],
    intent: dict[str, bool],
) -> str:

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

        return (
            "This assessment evaluates frontend engineering, "
            "JavaScript frameworks, UI development, and web application skills."
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

        return (
            "This assessment evaluates backend development, "
            "APIs, databases, Python, and server-side engineering skills."
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

        return (
            "This assessment evaluates machine learning, "
            "analytics, statistical reasoning, and data science capabilities."
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

        return (
            "This assessment evaluates communication, "
            "presentation, collaboration, and stakeholder interaction skills."
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

        return (
            "This assessment supports leadership, "
            "organizational strategy, and people management evaluation."
        )

    # =====================================================
    # COGNITIVE
    # =====================================================

    if (
        intent["cognitive"]
        and contains_any(
            text,
            COGNITIVE_KEYWORDS,
        )
    ):

        return (
            "This assessment evaluates logical reasoning, "
            "problem-solving, and analytical ability."
        )

    return (
        "This assessment matches the requested hiring requirements."
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
        return False

    text = build_searchable_text(item)

    # =====================================================
    # COMMUNICATION FIX
    # =====================================================

    if intent["communication"]:

        # reject telecom/electronics false positives
        if contains_any(
            text,
            IRRELEVANT_COMMUNICATION_CONTEXT,
        ):
            return False

        if not contains_any(
            text,
            COMMUNICATION_KEYWORDS,
        ):
            return False

    # =====================================================
    # FRONTEND FILTER
    # =====================================================

    if intent["frontend"]:

        if not contains_any(
            text,
            FRONTEND_KEYWORDS,
        ):
            return False

    # =====================================================
    # BACKEND FILTER
    # =====================================================

    if intent["backend"]:

        if not contains_any(
            text,
            BACKEND_KEYWORDS,
        ):
            return False

    # =====================================================
    # DATA SCIENCE FILTER
    # =====================================================

    if intent["data_science"]:

        if not contains_any(
            text,
            DATA_SCIENCE_KEYWORDS,
        ):
            return False

    # =====================================================
    # LEADERSHIP FILTER
    # =====================================================

    if intent["leadership"]:

        if not contains_any(
            text,
            LEADERSHIP_KEYWORDS,
        ):
            return False

    # =====================================================
    # COGNITIVE FILTER
    # =====================================================

    if intent["cognitive"]:

        if not (
            contains_any(
                text,
                COGNITIVE_KEYWORDS,
            )
            or item.get("test_type") == "A"
        ):
            return False

    return True


# =========================================================
# SCORE BOOSTING
# =========================================================


def apply_intent_boost(
    item: dict[str, Any],
    intent: dict[str, bool],
) -> float:

    text = build_searchable_text(item)

    boost = 0.0

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
        boost += 0.32

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
        boost += 0.30

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
        boost += 0.35

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
        boost += 0.35

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
        boost += 0.28

    # =====================================================
    # COGNITIVE
    # =====================================================

    if (
        intent["cognitive"]
        and (
            contains_any(
                text,
                COGNITIVE_KEYWORDS,
            )
            or item.get("test_type") == "A"
        )
    ):
        boost += 0.25

    return round(boost, 4)


# =========================================================
# ENRICH RESULT
# =========================================================


def enrich_result(
    item: dict[str, Any],
    intent: dict[str, bool],
) -> dict[str, Any]:

    enriched = dict(item)

    base_score = safe_float(
        item.get("score", 0.0)
    )

    boost = apply_intent_boost(
        item,
        intent,
    )

    test_type = item.get(
        "test_type",
        "K",
    )

    type_weight = TEST_TYPE_WEIGHTS.get(
        test_type,
        1.0,
    )

    final_score = min(
        (
            base_score + boost
        ) * type_weight,
        1.0,
    )

    final_score = round(
        final_score,
        4,
    )

    confidence = calibrate_confidence(
        final_score
    )

    enriched["score"] = final_score

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

    # =====================================================
    # FRONTEND SAFE DEFAULTS
    # =====================================================

    defaults = {
        "matched_roles": [],
        "matched_domains": [],
        "matched_competencies": [],
        "domains": [],
        "roles": [],
        "job_levels": [],
        "languages": [],
        "duration": None,
        "remote": None,
        "adaptive": None,
        "retrieval_metadata": None,
    }

    for key, value in defaults.items():
        enriched.setdefault(key, value)

    return enriched


# =========================================================
# DIVERSITY
# =========================================================


def enforce_diversity(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    final_results: list[
        dict[str, Any]
    ] = []

    seen_names: set[str] = set()

    type_counts = defaultdict(int)

    for item in results:

        raw_name = normalize(
            item.get("name", "")
        )

        root_name = (
            raw_name
            .replace("(new)", "")
            .replace("adaptive", "")
            .replace("pro", "")
            .replace("interactive", "")
            .strip()
        )

        if root_name in seen_names:
            continue

        seen_names.add(root_name)

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

        if not results:

            logger.warning(
                "No retrieval results received."
            )

            return []

        logger.info(
            "Incoming retrieval results: %s",
            len(results),
        )

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
            "Reranked results count: %s",
            len(ranked_results),
        )

        if not ranked_results:
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
                "No strict matches found. Using fallback results."
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

        # =================================================
        # VALIDATE
        # =================================================

        validated_results = (
            validate_recommendations(
                enriched_results
            )
        )

        if not validated_results:
            validated_results = enriched_results

        # =================================================
        # SORT
        # =================================================

        validated_results.sort(
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
            "Final recommendations: %s",
            [
                {
                    "name": item.get("name"),
                    "score": item.get("score"),
                    "confidence": item.get(
                        "confidence"
                    ),
                }
                for item in final_results
            ],
        )

        return final_results[
            :FINAL_RECOMMENDATIONS
        ]

    except Exception as error:

        logger.exception(
            "Recommendation generation failed: %s",
            error,
        )

        return []