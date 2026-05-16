# =========================================================
# app/services/reranker.py
# =========================================================

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.config.settings import (
    FINAL_RECOMMENDATIONS,
    HIGH_CONFIDENCE_THRESHOLD,
    KEYWORD_WEIGHT,
    MAX_SAME_TYPE_RESULTS,
    MIN_ACCEPTABLE_SCORE,
    QUERY_EXPANSIONS,
    ROLE_COMPETENCIES,
    ROLE_WEIGHT,
    SEMANTIC_WEIGHT,
    SOFT_SKILL_WEIGHT,
)

from app.utils.helpers import normalize

logger = logging.getLogger(__name__)

# =========================================================
# DOMAIN ONTOLOGY
# =========================================================

DOMAIN_ONTOLOGY = {
    "leadership": {
        "leadership",
        "leader",
        "management",
        "manager",
        "executive",
        "ownership",
        "stakeholder",
        "vision",
        "strategic",
        "decision making",
        "people management",
        "organizational",
        "business leadership",
    },

    "communication": {
        "communication",
        "presentation",
        "verbal",
        "written",
        "collaboration",
        "interpersonal",
        "stakeholder communication",
        "influence",
        "alignment",
        "facilitation",
        "negotiation",
    },

    "cognitive": {
        "cognitive",
        "reasoning",
        "analytical",
        "logical",
        "critical thinking",
        "problem solving",
        "numerical",
        "verbal reasoning",
        "deductive",
        "inductive",
        "analytics",
        "data analysis",
        "statistics",
    },

    "technical": {
        "technical",
        "software",
        "engineering",
        "coding",
        "programming",
        "cloud",
        "backend",
        "frontend",
        "python",
        "java",
        "sql",
        "system design",
        "machine learning",
        "ai",
        "data science",
        "data scientist",
    },

    "personality": {
        "personality",
        "behavioral",
        "behavioural",
        "motivation",
        "adaptability",
        "resilience",
        "culture fit",
        "work style",
        "occupational personality",
        "opq",
    },

    "product_management": {
        "product manager",
        "roadmap",
        "prioritization",
        "stakeholder",
        "execution",
        "ownership",
        "strategy",
        "vision",
        "cross functional",
        "business alignment",
    },
}

# =========================================================
# NEGATIVE SIGNALS
# =========================================================

NEGATIVE_SIGNALS = {
    "profile report",
    "development report",
    "feedback report",
}

# =========================================================
# TOKENIZATION
# =========================================================

def tokenize(
    text: str,
) -> set[str]:

    normalized = normalize(text)

    if not normalized:
        return set()

    return {
        token.strip()
        for token in normalized.split()
        if token.strip()
    }

# =========================================================
# QUERY ENRICHMENT
# =========================================================

def enrich_query(
    query: str,
) -> str:

    query = normalize(query)

    expansions: list[str] = []

    # =====================================================
    # QUERY EXPANSIONS
    # =====================================================

    for trigger, value in QUERY_EXPANSIONS.items():

        if trigger not in query:
            continue

        # support dict-based expansion structure
        if isinstance(value, dict):

            for terms in value.values():

                for item in terms:

                    if isinstance(item, tuple):
                        expansions.append(
                            normalize(item[0])
                        )

                    elif isinstance(item, str):
                        expansions.append(
                            normalize(item)
                        )

        elif isinstance(value, list):

            for item in value:

                if isinstance(item, tuple):
                    expansions.append(
                        normalize(item[0])
                    )

                elif isinstance(item, str):
                    expansions.append(
                        normalize(item)
                    )

    # =====================================================
    # ROLE COMPETENCIES
    # =====================================================

    for (
        role,
        competencies,
    ) in ROLE_COMPETENCIES.items():

        if normalize(role) not in query:
            continue

        expansions.extend(
            normalize(term)
            for term in competencies
        )

    # =====================================================
    # DATA SCIENCE BOOST
    # =====================================================

    if (
        "data scientist" in query
        or "data science" in query
    ):

        expansions.extend(
            [
                "machine learning",
                "analytics",
                "statistics",
                "reasoning",
                "problem solving",
                "python",
                "sql",
                "ai",
                "data analysis",
            ]
        )

    enriched_terms = list(
        dict.fromkeys(
            [
                query,
                *expansions,
            ]
        )
    )

    return normalize(
        " ".join(enriched_terms)
    )

# =========================================================
# TERM OVERLAP
# =========================================================

def compute_overlap(
    query_terms: set[str],
    doc_terms: set[str],
) -> float:

    if not query_terms:
        return 0.0

    overlap = query_terms & doc_terms

    if not overlap:
        return 0.0

    return round(
        len(overlap)
        / max(len(query_terms), 1),
        4,
    )

# =========================================================
# ONTOLOGY MATCHING
# =========================================================

def compute_ontology_score(
    query_terms: set[str],
    doc_terms: set[str],
) -> float:

    score = 0.0

    ontology_weights = {
        "leadership": 0.30,
        "communication": 0.22,
        "cognitive": 0.22,
        "technical": 0.22,
        "personality": 0.20,
        "product_management": 0.35,
    }

    for (
        domain,
        ontology_terms,
    ) in DOMAIN_ONTOLOGY.items():

        query_match = bool(
            query_terms & ontology_terms
        )

        doc_match = bool(
            doc_terms & ontology_terms
        )

        if query_match and doc_match:

            score += ontology_weights[
                domain
            ]

    return round(
        min(score, 0.85),
        4,
    )

# =========================================================
# TEST TYPE BOOST
# =========================================================

def compute_test_type_score(
    query: str,
    test_type: str,
) -> float:

    query = normalize(query)
    test_type = normalize(test_type)

    score = 0.0

    if any(
        term in query
        for term in {
            "leadership",
            "manager",
            "stakeholder",
        }
    ):

        if test_type == "l":
            score += 0.35

        if test_type == "p":
            score += 0.10

    if any(
        term in query
        for term in {
            "cognitive",
            "analytical",
            "problem solving",
            "reasoning",
            "data scientist",
            "machine learning",
        }
    ):

        if test_type == "c":
            score += 0.30

    if any(
        term in query
        for term in {
            "technical",
            "coding",
            "software",
            "python",
            "sql",
            "ai",
            "machine learning",
        }
    ):

        if test_type == "k":
            score += 0.30

    if any(
        term in query
        for term in {
            "communication",
            "presentation",
        }
    ):

        if test_type == "s":
            score += 0.20

    if any(
        term in query
        for term in {
            "personality",
            "behavioral",
        }
    ):

        if test_type == "p":
            score += 0.30

    return round(score, 4)

# =========================================================
# METADATA BOOST
# =========================================================

def compute_metadata_boost(
    item: dict[str, Any],
    query_terms: set[str],
) -> float:

    boost = 0.0

    roles = tokenize(
        " ".join(
            item.get("roles", [])
        )
    )

    domains = tokenize(
        " ".join(
            item.get("domains", [])
        )
    )

    if query_terms & roles:
        boost += 0.10

    if query_terms & domains:
        boost += 0.08

    return round(boost, 4)

# =========================================================
# PENALTY
# =========================================================

def compute_penalty(
    text: str,
) -> float:

    normalized = normalize(text)

    penalty = 0.0

    for signal in NEGATIVE_SIGNALS:

        if signal in normalized:
            penalty += 0.08

    return round(penalty, 4)

# =========================================================
# CONFIDENCE
# =========================================================

def compute_confidence(
    score: float,
) -> float:

    return round(
        min(max(score, 0.0), 1.0),
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

        normalized_name = normalize(
            item.get("name", "")
        )

        root = (
            normalized_name
            .replace("(new)", "")
            .replace("interactive", "")
            .replace("simulation", "")
            .strip()
        )

        if not root:
            continue

        if root in seen:
            continue

        seen.add(root)

        unique.append(item)

    return unique

# =========================================================
# MAIN RERANKER
# =========================================================

def rerank_results(
    results: list[dict[str, Any]],
    query: str,
) -> list[dict[str, Any]]:

    try:

        if not results:
            logger.warning(
                "No retrieval results provided."
            )
            return []

        enriched_query = enrich_query(
            query
        )

        query_terms = tokenize(
            enriched_query
        )

        logger.info(
            "Enriched query: %s",
            enriched_query,
        )

        logger.info(
            "Query terms: %s",
            sorted(query_terms),
        )

        reranked: list[dict[str, Any]] = []

        for item in results:

            combined_text = normalize(
                " ".join(
                    [
                        item.get(
                            "name",
                            "",
                        ),
                        item.get(
                            "description",
                            "",
                        ),
                        item.get(
                            "combined_text",
                            "",
                        ),
                        " ".join(
                            item.get(
                                "roles",
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
                                "skills",
                                [],
                            )
                        ),
                    ]
                )
            )

            doc_terms = tokenize(
                combined_text
            )

            semantic_score = float(
                item.get(
                    "score",
                    0.50,
                )
            )

            keyword_score = compute_overlap(
                query_terms,
                doc_terms,
            )

            ontology_score = (
                compute_ontology_score(
                    query_terms,
                    doc_terms,
                )
            )

            type_score = (
                compute_test_type_score(
                    enriched_query,
                    item.get(
                        "test_type",
                        "",
                    ),
                )
            )

            metadata_score = (
                compute_metadata_boost(
                    item,
                    query_terms,
                )
            )

            penalty = compute_penalty(
                combined_text
            )

            # =================================================
            # FINAL SCORE
            # =================================================

            final_score = (
                (
                    semantic_score
                    * SEMANTIC_WEIGHT
                )
                + (
                    keyword_score
                    * KEYWORD_WEIGHT
                )
                + (
                    ontology_score
                    * ROLE_WEIGHT
                )
                + (
                    (
                        type_score
                        + metadata_score
                    )
                    * SOFT_SKILL_WEIGHT
                )
                - penalty
            )

            # =================================================
            # DATA SCIENCE SAFETY BOOST
            # =================================================

            if (
                "data scientist"
                in enriched_query
            ):

                if any(
                    term in combined_text
                    for term in {
                        "machine learning",
                        "analytics",
                        "reasoning",
                        "python",
                        "sql",
                        "data",
                    }
                ):
                    final_score += 0.12

            final_score = round(
                max(
                    min(final_score, 1.0),
                    0.0,
                ),
                4,
            )

            logger.info(
                "Rerank item=%s semantic=%.4f keyword=%.4f ontology=%.4f type=%.4f metadata=%.4f penalty=%.4f final=%.4f",
                item.get("name"),
                semantic_score,
                keyword_score,
                ontology_score,
                type_score,
                metadata_score,
                penalty,
                final_score,
            )

            # =================================================
            # RELAXED FILTER
            # =================================================

            dynamic_threshold = max(
                MIN_ACCEPTABLE_SCORE * 0.6,
                0.18,
            )

            if final_score < dynamic_threshold:

                logger.info(
                    "Rejected %s due to low score %.4f",
                    item.get("name"),
                    final_score,
                )

                continue

            enriched_item = dict(item)

            enriched_item[
                "score"
            ] = final_score

            enriched_item[
                "confidence"
            ] = compute_confidence(
                final_score
            )

            enriched_item[
                "recommendation_strength"
            ] = (
                "high"
                if final_score
                >= HIGH_CONFIDENCE_THRESHOLD
                else (
                    "medium"
                    if final_score >= 0.55
                    else "low"
                )
            )

            reranked.append(
                enriched_item
            )

        # =====================================================
        # SORT
        # =====================================================

        reranked.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        reranked = deduplicate_results(
            reranked
        )

        # =====================================================
        # DIVERSITY FILTER
        # =====================================================

        final_results: list[
            dict[str, Any]
        ] = []

        type_counts = defaultdict(int)

        for item in reranked:

            test_type = normalize(
                item.get(
                    "test_type",
                    "k",
                )
            )

            if (
                type_counts[test_type]
                >= MAX_SAME_TYPE_RESULTS
            ):
                continue

            type_counts[
                test_type
            ] += 1

            final_results.append(item)

            if (
                len(final_results)
                >= FINAL_RECOMMENDATIONS
            ):
                break

        logger.info(
            "Final reranked results: %s",
            [
                {
                    "name": x.get("name"),
                    "score": x.get("score"),
                }
                for x in final_results
            ],
        )

        return final_results

    except Exception as error:

        logger.exception(
            "Reranking failed: %s",
            error,
        )

        return []