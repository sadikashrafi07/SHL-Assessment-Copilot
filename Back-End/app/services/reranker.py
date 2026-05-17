# =========================================================
# app/services/reranker.py
# Production-Grade Hybrid Reranker
# Fully Fixed + Accurate Intent-Aware Ranking
# =========================================================

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any

from app.config.settings import (
    FINAL_RECOMMENDATIONS,
    HIGH_CONFIDENCE_THRESHOLD,
    MAX_SAME_TYPE_RESULTS,
)

from app.utils.helpers import normalize

logger = logging.getLogger(__name__)

# =========================================================
# DOMAIN VOCABULARY
# =========================================================

DOMAIN_TERMS: dict[str, set[str]] = {

    "technical": {
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "angular",
        "vue",
        "sql",
        "coding",
        "software",
        "backend",
        "frontend",
        "cloud",
        "api",
        "microservices",
        "machine learning",
        "data science",
        "ai",
        "analytics",
        "engineering",
    },

    "leadership": {
        "leadership",
        "stakeholder",
        "management",
        "strategy",
        "decision making",
        "people management",
        "executive",
        "organizational",
        "ownership",
        "director",
        "manager",
    },

    "communication": {
        "communication",
        "presentation",
        "verbal",
        "written",
        "collaboration",
        "influence",
        "negotiation",
        "stakeholder communication",
        "interpersonal",
        "listening",
    },

    "cognitive": {
        "reasoning",
        "analytical",
        "logical",
        "critical thinking",
        "problem solving",
        "numerical",
        "deductive",
        "statistics",
        "inductive",
    },

    "personality": {
        "personality",
        "behavioral",
        "adaptability",
        "motivation",
        "resilience",
        "opq",
    },
}

# =========================================================
# HARD NEGATIVE TERMS
# =========================================================

NEGATIVE_TERMS = {
    "feedback report",
    "development report",
    "profile report",
}

# =========================================================
# FALSE POSITIVE FILTERS
# =========================================================

IRRELEVANT_COMMUNICATION_TERMS = {
    "telecommunication",
    "telecommunications",
    "microwave",
    "signal processing",
    "network engineering",
    "instrumentation",
    "semiconductor",
    "electronics",
}

# =========================================================
# INTENT MAP
# =========================================================

INTENT_KEYWORDS = {

    "frontend": {
        "frontend",
        "react",
        "angular",
        "vue",
        "javascript",
        "typescript",
        "ui",
        "ux",
        "css",
        "html",
    },

    "backend": {
        "backend",
        "python",
        "java",
        "api",
        "microservices",
        "django",
        "fastapi",
        "spring",
        "database",
        "sql",
    },

    "data_science": {
        "machine learning",
        "data science",
        "analytics",
        "statistics",
        "ai",
        "nlp",
        "deep learning",
        "predictive",
    },

    "leadership": {
        "leadership",
        "manager",
        "director",
        "executive",
        "stakeholder",
        "ownership",
        "strategy",
    },

    "communication": {
        "communication",
        "presentation",
        "stakeholder",
        "collaboration",
        "written",
        "verbal",
        "interpersonal",
    },

    "cognitive": {
        "reasoning",
        "logical",
        "deductive",
        "analytical",
        "critical thinking",
        "problem solving",
        "numerical",
    },
}

# =========================================================
# TOKENIZER
# =========================================================

TOKEN_SPLIT_REGEX = re.compile(r"[\s,/|;:.()\[\]{}]+")


def tokenize(text: str) -> set[str]:

    if not text:
        return set()

    normalized = normalize(text)

    return {
        token.strip()
        for token in TOKEN_SPLIT_REGEX.split(normalized)
        if token.strip()
    }

# =========================================================
# QUERY EXPANSION
# =========================================================

def enrich_query(query: str) -> str:

    query = normalize(query)

    expansions: list[str] = []

    # =====================================================
    # FRONTEND
    # =====================================================

    if any(
        term in query
        for term in [
            "frontend",
            "ui engineer",
            "react",
            "vue",
            "angular",
        ]
    ):

        expansions.extend([
            "javascript",
            "typescript",
            "ui",
            "ux",
            "web",
            "frontend",
            "react",
            "css",
        ])

    # =====================================================
    # BACKEND
    # =====================================================

    if any(
        term in query
        for term in [
            "backend",
            "python",
            "java",
            "api",
        ]
    ):

        expansions.extend([
            "backend",
            "sql",
            "database",
            "microservices",
            "api",
            "server",
        ])

    # =====================================================
    # DATA SCIENCE
    # =====================================================

    if any(
        term in query
        for term in [
            "data scientist",
            "machine learning",
            "ai",
            "analytics",
        ]
    ):

        expansions.extend([
            "machine learning",
            "statistics",
            "python",
            "sql",
            "analytics",
            "reasoning",
            "nlp",
            "data science",
        ])

    # =====================================================
    # LEADERSHIP
    # =====================================================

    if any(
        term in query
        for term in [
            "manager",
            "director",
            "leadership",
            "executive",
        ]
    ):

        expansions.extend([
            "leadership",
            "strategy",
            "stakeholder management",
            "people management",
            "decision making",
        ])

    # =====================================================
    # COMMUNICATION
    # =====================================================

    if "communication" in query:

        expansions.extend([
            "presentation",
            "verbal communication",
            "written communication",
            "interpersonal communication",
            "collaboration",
        ])

    return normalize(
        f"{query} {' '.join(expansions)}"
    )

# =========================================================
# INTENT DETECTION
# =========================================================

def infer_query_intent(
    query: str,
) -> dict[str, bool]:

    query = normalize(query)

    intent_map: dict[str, bool] = {}

    for intent, keywords in INTENT_KEYWORDS.items():

        intent_map[intent] = any(
            keyword in query
            for keyword in keywords
        )

    return intent_map

# =========================================================
# KEYWORD OVERLAP
# =========================================================

def keyword_overlap_score(
    query_terms: set[str],
    doc_terms: set[str],
) -> float:

    if not query_terms or not doc_terms:
        return 0.0

    overlap = query_terms.intersection(doc_terms)

    if not overlap:
        return 0.0

    return round(
        min(
            len(overlap) / len(query_terms),
            1.0,
        ),
        4,
    )

# =========================================================
# DOMAIN SCORE
# =========================================================

def domain_score(
    query_terms: set[str],
    doc_terms: set[str],
) -> float:

    score = 0.0

    for terms in DOMAIN_TERMS.values():

        query_match = bool(
            query_terms.intersection(terms)
        )

        doc_match = bool(
            doc_terms.intersection(terms)
        )

        if query_match and doc_match:
            score += 0.12

    return min(score, 0.50)

# =========================================================
# TEST TYPE BOOST
# =========================================================

def test_type_boost(
    intent: dict[str, bool],
    test_type: str,
) -> float:

    test_type = str(
        test_type or "K"
    ).upper()

    boost = 0.0

    # =====================================================
    # TECHNICAL
    # =====================================================

    if (
        intent["frontend"]
        or intent["backend"]
        or intent["data_science"]
    ):

        if test_type == "K":
            boost += 0.18

    # =====================================================
    # COMMUNICATION
    # =====================================================

    if intent["communication"]:

        if test_type == "A":
            boost += 0.16

    # =====================================================
    # LEADERSHIP
    # =====================================================

    if intent["leadership"]:

        if test_type in {"L", "P"}:
            boost += 0.20

    # =====================================================
    # COGNITIVE
    # =====================================================

    if intent["cognitive"]:

        if test_type == "A":
            boost += 0.14

    return min(boost, 0.25)

# =========================================================
# NEGATIVE PENALTY
# =========================================================

def penalty_score(
    text: str,
    intent: dict[str, bool],
) -> float:

    normalized = normalize(text)

    penalty = 0.0

    # =====================================================
    # GENERIC NEGATIVES
    # =====================================================

    for term in NEGATIVE_TERMS:

        if term in normalized:
            penalty += 0.10

    # =====================================================
    # COMMUNICATION FALSE POSITIVES
    # =====================================================

    if intent["communication"]:

        for term in IRRELEVANT_COMMUNICATION_TERMS:

            if term in normalized:
                penalty += 0.45

    return penalty

# =========================================================
# SPECIALIZED BOOSTS
# =========================================================

def apply_specialized_boosts(
    score: float,
    text: str,
    intent: dict[str, bool],
) -> float:

    normalized = normalize(text)

    # =====================================================
    # FRONTEND
    # =====================================================

    if intent["frontend"]:

        if any(
            term in normalized
            for term in [
                "react",
                "javascript",
                "typescript",
                "frontend",
            ]
        ):
            score += 0.15

    # =====================================================
    # BACKEND
    # =====================================================

    if intent["backend"]:

        if any(
            term in normalized
            for term in [
                "python",
                "backend",
                "api",
                "sql",
            ]
        ):
            score += 0.15

    # =====================================================
    # DATA SCIENCE
    # =====================================================

    if intent["data_science"]:

        if any(
            term in normalized
            for term in [
                "machine learning",
                "analytics",
                "statistics",
                "data science",
            ]
        ):
            score += 0.18

    # =====================================================
    # LEADERSHIP
    # =====================================================

    if intent["leadership"]:

        if any(
            term in normalized
            for term in [
                "leadership",
                "stakeholder",
                "executive",
            ]
        ):
            score += 0.16

    # =====================================================
    # COMMUNICATION
    # =====================================================

    if intent["communication"]:

        if any(
            term in normalized
            for term in [
                "business communication",
                "interpersonal communication",
                "written communication",
                "verbal communication",
            ]
        ):
            score += 0.22

    return score

# =========================================================
# CONFIDENCE
# =========================================================

def compute_confidence(
    score: float,
) -> float:

    score = max(
        min(score, 1.0),
        0.0,
    )

    confidence = 0.50 + (score * 0.45)

    return round(
        min(confidence, 0.99),
        2,
    )

# =========================================================
# DEDUPLICATION
# =========================================================

def deduplicate_results(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    unique: list[dict[str, Any]] = []

    seen: set[str] = set()

    for item in results:

        name = normalize(
            item.get("name", "")
        )

        canonical = (
            name
            .replace("(new)", "")
            .replace("2.0", "")
            .replace("1.0", "")
            .replace("interactive", "")
            .replace("simulation", "")
            .replace("automata", "")
            .strip()
        )

        if canonical in seen:
            continue

        seen.add(canonical)

        unique.append(item)

    return unique

# =========================================================
# BUILD SEARCH TEXT
# =========================================================

def build_searchable_text(
    item: dict[str, Any],
) -> str:

    parts: list[str] = []

    scalar_fields = [
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
    ]

    for field in scalar_fields:

        value = item.get(field)

        if value:
            parts.append(str(value))

    for field in list_fields:

        values = item.get(field, [])

        if isinstance(values, list):
            parts.extend(
                str(v)
                for v in values
                if v
            )

    return normalize(" ".join(parts))

# =========================================================
# MAIN RERANKER
# =========================================================

def rerank_results(
    results: list[dict[str, Any]],
    query: str,
) -> list[dict[str, Any]]:

    try:

        if not results:
            return []

        enriched_query = enrich_query(query)

        intent = infer_query_intent(
            enriched_query
        )

        query_terms = tokenize(
            enriched_query
        )

        reranked: list[dict[str, Any]] = []

        for item in results:

            searchable_text = (
                build_searchable_text(item)
            )

            doc_terms = tokenize(
                searchable_text
            )

            semantic_score = float(
                item.get("score", 0.0)
            )

            keyword_score = (
                keyword_overlap_score(
                    query_terms,
                    doc_terms,
                )
            )

            ontology_score = (
                domain_score(
                    query_terms,
                    doc_terms,
                )
            )

            type_score = (
                test_type_boost(
                    intent,
                    item.get(
                        "test_type",
                        "K",
                    ),
                )
            )

            penalty = penalty_score(
                searchable_text,
                intent,
            )

            # =================================================
            # FINAL WEIGHTED SCORE
            # =================================================

            final_score = (

                semantic_score * 0.45

                +

                keyword_score * 0.25

                +

                ontology_score * 0.15

                +

                type_score * 0.15

                -

                penalty
            )

            # =================================================
            # SPECIALIZED BOOSTS
            # =================================================

            final_score = (
                apply_specialized_boosts(
                    final_score,
                    searchable_text,
                    intent,
                )
            )

            final_score = max(
                min(final_score, 1.0),
                0.0,
            )

            enriched = dict(item)

            enriched["score"] = round(
                final_score,
                4,
            )

            confidence = compute_confidence(
                final_score
            )

            enriched["confidence"] = confidence

            enriched[
                "recommendation_strength"
            ] = (
                "high"
                if confidence
                >= HIGH_CONFIDENCE_THRESHOLD
                else (
                    "medium"
                    if confidence >= 0.65
                    else "low"
                )
            )

            reranked.append(enriched)

        # =====================================================
        # SORT
        # =====================================================

        reranked.sort(
            key=lambda x: (
                x.get("score", 0.0),
                x.get("confidence", 0.0),
            ),
            reverse=True,
        )

        # =====================================================
        # DEDUP
        # =====================================================

        reranked = deduplicate_results(
            reranked
        )

        # =====================================================
        # DIVERSITY CONTROL
        # =====================================================

        final_results: list[
            dict[str, Any]
        ] = []

        type_counts = defaultdict(int)

        for item in reranked:

            test_type = str(
                item.get(
                    "test_type",
                    "K",
                )
            ).upper()

            if (
                type_counts[test_type]
                >= MAX_SAME_TYPE_RESULTS
            ):
                continue

            type_counts[test_type] += 1

            final_results.append(item)

            if (
                len(final_results)
                >= FINAL_RECOMMENDATIONS
            ):
                break

        logger.info(
            "Final reranked results: %s",
            [
                (
                    item.get("name"),
                    item.get("score"),
                )
                for item in final_results
            ],
        )

        return final_results

    except Exception as error:

        logger.exception(
            "Reranking failed: %s",
            error,
        )

        return []