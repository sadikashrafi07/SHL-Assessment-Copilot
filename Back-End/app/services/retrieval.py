# =========================================================
# app/services/retrieval.py
# ENTERPRISE HYBRID RETRIEVAL ENGINE
# ULTRA HIGH ACCURACY + LOW LATENCY + RAILWAY OPTIMIZED
# ASSIGNMENT OPTIMIZED HYBRID SEARCH ARCHITECTURE
# =========================================================

from __future__ import annotations

import json
import logging
import math
import os
import re

from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from fastembed import TextEmbedding
from rank_bm25 import BM25Okapi

from app.config.settings import (
    BM25_WEIGHT,
    COMPETENCY_WEIGHT,
    DOMAIN_WEIGHT,
    EMBEDDING_NORMALIZE,
    ENABLE_BM25,
    ENABLE_HYBRID_RETRIEVAL,
    FINAL_RECOMMENDATIONS,
    HIGH_CONFIDENCE_THRESHOLD,
    MAX_SAME_TYPE_RESULTS,
    MIN_ACCEPTABLE_SCORE,
    MIN_SIMILARITY_THRESHOLD,
    QUERY_EXPANSIONS,
    ROLE_COMPETENCIES,
    ROLE_WEIGHT,
    SEMANTIC_WEIGHT,
    SENIORITY_WEIGHT,
    TOP_K_BM25,
    TOP_K_HYBRID,
    TOP_K_SEMANTIC,
    VALID_TEST_TYPES,
)

from app.utils.helpers import normalize

# =========================================================
# ENVIRONMENT
# =========================================================

os.environ["TOKENIZERS_PARALLELISM"] = "false"

logger = logging.getLogger(__name__)

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

CATALOG_PATH = DATA_DIR / "cleaned_catalog.json"

EMBEDDINGS_PATH = DATA_DIR / "catalog_embeddings.npy"

# =========================================================
# TOKENIZATION
# =========================================================

TOKEN_SPLIT_REGEX = re.compile(
    r"[\s,/|;:.()\[\]{}_\-+]+"
)

# =========================================================
# DOMAIN VOCABULARIES
# =========================================================

TECH_KEYWORDS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "angular",
    "vue",
    "node",
    "nodejs",
    "backend",
    "frontend",
    "fullstack",
    "full stack",
    "fastapi",
    "django",
    "flask",
    "microservices",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "cloud",
    "api",
    "sql",
    "database",
    "software engineer",
    "developer",
}

DATA_KEYWORDS = {
    "machine learning",
    "deep learning",
    "ai",
    "analytics",
    "nlp",
    "statistics",
    "data science",
    "classification",
    "regression",
    "predictive",
}

LEADERSHIP_KEYWORDS = {
    "leadership",
    "management",
    "ownership",
    "stakeholder",
    "strategy",
    "manager",
    "executive",
}

COMMUNICATION_KEYWORDS = {
    "communication",
    "presentation",
    "verbal",
    "written",
    "collaboration",
    "interpersonal",
}

COGNITIVE_KEYWORDS = {
    "problem solving",
    "critical thinking",
    "reasoning",
    "analytical",
    "logical",
    "numerical",
}

NEGATIVE_ENGINEERING_DOMAINS = {
    "telecommunications",
    "telecommunication",
    "instrumentation",
    "electronics",
    "electrical",
    "mechanical",
    "civil engineering",
    "semiconductor",
    "signal processing",
    "microwave",
    "manufacturing",
}

# =========================================================
# LOAD CATALOG
# =========================================================

def load_catalog() -> list[dict[str, Any]]:

    with open(
        CATALOG_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Catalog must be a list"
        )

    return data


CATALOG = load_catalog()

# =========================================================
# NORMALIZATION
# =========================================================

@lru_cache(maxsize=10000)
def cached_normalize(
    text: str,
) -> str:

    return normalize(text or "")


# =========================================================
# TOKENIZER
# =========================================================

@lru_cache(maxsize=10000)
def tokenize(
    text: str,
) -> frozenset[str]:

    if not text:
        return frozenset()

    normalized = cached_normalize(text)

    tokens = {
        token.strip()
        for token in TOKEN_SPLIT_REGEX.split(
            normalized
        )
        if token.strip()
    }

    return frozenset(tokens)


# =========================================================
# SAFE FLOAT
# =========================================================

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


# =========================================================
# EMBEDDINGS
# =========================================================

@lru_cache(maxsize=1)
def get_catalog_embeddings():

    embeddings = np.load(
        EMBEDDINGS_PATH,
        mmap_mode="r",
    ).astype(np.float32)

    if EMBEDDING_NORMALIZE:

        norms = np.linalg.norm(
            embeddings,
            axis=1,
            keepdims=True,
        )

        norms[norms == 0] = 1.0

        embeddings = embeddings / norms

    return embeddings


@lru_cache(maxsize=1)
def get_embedding_model():

    return TextEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )


# =========================================================
# DOCUMENT TEXT
# =========================================================

def build_document_text(
    item: dict[str, Any],
) -> str:

    parts: list[str] = []

    weighted_fields = [
        ("name", 6),
        ("summary", 5),
        ("description", 4),
    ]

    list_fields = [
        ("roles", 5),
        ("domains", 4),
        ("job_levels", 4),
        ("skills", 5),
        ("competencies", 5),
        ("expanded_competencies", 5),
        ("technical_skills", 6),
        ("communication_skills", 4),
        ("leadership_traits", 4),
        ("cognitive_traits", 4),
        ("personality_traits", 2),
        ("tags", 3),
    ]

    # ============================================
    # SCALAR FIELDS WITH TERM BOOSTING
    # ============================================

    for field, weight in weighted_fields:

        value = item.get(field)

        if value:

            text = str(value)

            boosted = " ".join(
                [text] * weight
            )

            parts.append(boosted)

    # ============================================
    # LIST FIELDS WITH TERM BOOSTING
    # ============================================

    for field, weight in list_fields:

        values = item.get(field, [])

        if not isinstance(values, list):
            continue

        for value in values:

            if not value:
                continue

            boosted = " ".join(
                [str(value)] * weight
            )

            parts.append(boosted)

    return cached_normalize(
        " ".join(parts)
    )


DOCUMENTS = [
    build_document_text(item)
    for item in CATALOG
]

# =========================================================
# BM25
# =========================================================

TOKENIZED_CORPUS = [
    doc.split()
    for doc in DOCUMENTS
]

BM25 = BM25Okapi(
    TOKENIZED_CORPUS
)

# =========================================================
# QUERY EXPANSION
# =========================================================

def expand_query(
    query: str,
) -> str:

    query = cached_normalize(query)

    expansions: list[str] = [query]

    # ============================================
    # DIRECT EXPANSIONS
    # ============================================

    for trigger, terms in QUERY_EXPANSIONS.items():

        if trigger in query:
            expansions.extend(terms)

    # ============================================
    # ROLE EXPANSIONS
    # ============================================

    for role, competencies in ROLE_COMPETENCIES.items():

        if role in query:
            expansions.extend(
                competencies
            )

    # ============================================
    # TECH EXPANSIONS
    # ============================================

    if any(
        keyword in query
        for keyword in TECH_KEYWORDS
    ):

        expansions.extend(
            [
                "coding",
                "programming",
                "technical assessment",
                "software development",
                "problem solving",
                "backend engineering",
                "frontend engineering",
            ]
        )

    # ============================================
    # DATA EXPANSIONS
    # ============================================

    if any(
        keyword in query
        for keyword in DATA_KEYWORDS
    ):

        expansions.extend(
            [
                "machine learning",
                "analytics",
                "data science",
                "statistics",
            ]
        )

    # ============================================
    # LEADERSHIP EXPANSIONS
    # ============================================

    if any(
        keyword in query
        for keyword in LEADERSHIP_KEYWORDS
    ):

        expansions.extend(
            [
                "management",
                "stakeholder",
                "ownership",
                "leadership",
            ]
        )

    # ============================================
    # COMMUNICATION EXPANSIONS
    # ============================================

    if any(
        keyword in query
        for keyword in COMMUNICATION_KEYWORDS
    ):

        expansions.extend(
            [
                "communication",
                "presentation",
                "collaboration",
            ]
        )

    deduped = list(
        dict.fromkeys(
            cached_normalize(term)
            for term in expansions
            if term
        )
    )

    return " ".join(deduped)


# =========================================================
# EMBEDDING
# =========================================================

def embed_query(
    query: str,
) -> np.ndarray:

    model = get_embedding_model()

    embedding = list(
        model.embed([query])
    )[0]

    embedding = np.array(
        embedding,
        dtype=np.float32,
    )

    if EMBEDDING_NORMALIZE:

        norm = np.linalg.norm(
            embedding
        )

        if norm > 0:
            embedding = (
                embedding / norm
            )

    return embedding


# =========================================================
# SEMANTIC SEARCH
# =========================================================

def semantic_search(
    query: str,
    top_k: int = TOP_K_SEMANTIC,
):

    embeddings = (
        get_catalog_embeddings()
    )

    query_embedding = embed_query(
        query
    )

    similarities = (
        embeddings @ query_embedding
    )

    top_indices = np.argsort(
        similarities
    )[::-1][:top_k]

    results = []

    for idx in top_indices:

        score = float(
            similarities[idx]
        )

        if score < MIN_SIMILARITY_THRESHOLD:
            continue

        results.append(
            (
                int(idx),
                round(score, 4),
            )
        )

    return results


# =========================================================
# BM25 SEARCH
# =========================================================

def bm25_search(
    query: str,
    top_k: int = TOP_K_BM25,
):

    if not ENABLE_BM25:
        return []

    tokens = query.split()

    if not tokens:
        return []

    scores = BM25.get_scores(tokens)

    if len(scores) == 0:
        return []

    max_score = max(scores)

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True,
    )

    results = []

    for idx, score in ranked[:top_k]:

        normalized_score = (
            score / max_score
            if max_score > 0
            else 0.0
        )

        results.append(
            (
                idx,
                round(
                    float(normalized_score),
                    4,
                ),
            )
        )

    return results


# =========================================================
# ROLE MATCH SCORE
# =========================================================

def role_match_score(
    query: str,
    item: dict[str, Any],
) -> float:

    query_tokens = tokenize(query)

    roles = item.get(
        "roles",
        [],
    )

    if not roles:
        return 0.0

    best = 0.0

    for role in roles:

        role_tokens = tokenize(role)

        if not role_tokens:
            continue

        overlap = len(
            query_tokens & role_tokens
        )

        union = len(
            query_tokens | role_tokens
        )

        score = (
            overlap / union
            if union > 0
            else 0.0
        )

        best = max(best, score)

    return round(best, 4)


# =========================================================
# COMPETENCY MATCH SCORE
# =========================================================

def competency_match_score(
    query: str,
    item: dict[str, Any],
) -> float:

    query_tokens = tokenize(query)

    competencies = []

    competency_fields = [
        "technical_skills",
        "expanded_competencies",
        "communication_skills",
        "leadership_traits",
        "cognitive_traits",
    ]

    for field in competency_fields:

        competencies.extend(
            item.get(field, [])
        )

    if not competencies:
        return 0.0

    matches = 0
    total = 0

    for competency in competencies:

        comp_tokens = tokenize(
            competency
        )

        if not comp_tokens:
            continue

        total += 1

        overlap = len(
            query_tokens & comp_tokens
        )

        if overlap > 0:
            matches += overlap / len(
                comp_tokens
            )

    if total == 0:
        return 0.0

    score = matches / total

    return round(
        min(score * 2.2, 1.0),
        4,
    )


# =========================================================
# SENIORITY SCORE
# =========================================================

def seniority_score(
    query: str,
    item: dict[str, Any],
) -> float:

    query_norm = cached_normalize(
        query
    )

    levels = item.get(
        "job_levels",
        [],
    )

    if not levels:
        return 0.0

    for level in levels:

        level_norm = cached_normalize(
            level
        )

        if level_norm in query_norm:
            return 1.0

    return 0.0


# =========================================================
# NEGATIVE PENALTY
# =========================================================

def negative_penalty(
    query: str,
    item: dict[str, Any],
) -> float:

    query_norm = cached_normalize(
        query
    )

    searchable = build_document_text(
        item
    )

    penalty = 0.0

    software_query = any(
        keyword in query_norm
        for keyword in TECH_KEYWORDS
    )

    if software_query:

        negative_hits = sum(
            domain in searchable
            for domain in NEGATIVE_ENGINEERING_DOMAINS
        )

        penalty += min(
            negative_hits * 0.08,
            0.30,
        )

    return round(penalty, 4)


# =========================================================
# DOMAIN BOOST
# =========================================================

def ontology_boost(
    query: str,
    item: dict[str, Any],
) -> float:

    query_norm = cached_normalize(
        query
    )

    searchable = build_document_text(
        item
    )

    boost = 0.0

    groups = [
        (TECH_KEYWORDS, 0.035, 0.25),
        (DATA_KEYWORDS, 0.04, 0.20),
        (LEADERSHIP_KEYWORDS, 0.03, 0.15),
        (COMMUNICATION_KEYWORDS, 0.03, 0.15),
        (COGNITIVE_KEYWORDS, 0.03, 0.15),
    ]

    for keywords, factor, cap in groups:

        if any(
            term in query_norm
            for term in keywords
        ):

            hits = sum(
                term in searchable
                for term in keywords
            )

            boost += min(
                hits * factor,
                cap,
            )

    return round(
        min(boost, 0.40),
        4,
    )


# =========================================================
# HYBRID FUSION
# =========================================================

def hybrid_fusion(
    query: str,
    semantic_results,
    bm25_results,
):

    semantic_map = dict(
        semantic_results
    )

    bm25_map = dict(
        bm25_results
    )

    all_doc_ids = (
        set(semantic_map.keys())
        | set(bm25_map.keys())
    )

    fused_results = []

    for doc_id in all_doc_ids:

        item = CATALOG[doc_id]

        semantic_score = semantic_map.get(
            doc_id,
            0.0,
        )

        bm25_score = bm25_map.get(
            doc_id,
            0.0,
        )

        role_score = role_match_score(
            query,
            item,
        )

        competency_score = (
            competency_match_score(
                query,
                item,
            )
        )

        seniority_match = (
            seniority_score(
                query,
                item,
            )
        )

        ontology_score = ontology_boost(
            query,
            item,
        )

        penalty = negative_penalty(
            query,
            item,
        )

        # ============================================
        # HYBRID WEIGHTED SCORE
        # ============================================

        final_score = (

            semantic_score
            * SEMANTIC_WEIGHT

            +

            bm25_score
            * BM25_WEIGHT

            +

            role_score
            * ROLE_WEIGHT

            +

            competency_score
            * COMPETENCY_WEIGHT

            +

            seniority_match
            * SENIORITY_WEIGHT

            +

            ontology_score
            * DOMAIN_WEIGHT
        )

        # ============================================
        # EXACT ROLE BOOST
        # ============================================

        if role_score >= 0.75:
            final_score += 0.10

        # ============================================
        # HIGH SKILL ALIGNMENT BOOST
        # ============================================

        if competency_score >= 0.40:
            final_score += 0.08

        # ============================================
        # STRONG SEMANTIC + BM25 AGREEMENT BOOST
        # ============================================

        if (
            semantic_score >= 0.65
            and bm25_score >= 0.50
        ):
            final_score += 0.07

        # ============================================
        # NEGATIVE DOMAIN PENALTY
        # ============================================

        final_score -= penalty

        final_score = max(
            min(final_score, 1.0),
            0.0,
        )

        fused_results.append(
            (
                doc_id,
                round(final_score, 4),
            )
        )

    fused_results.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    return fused_results[
        :TOP_K_HYBRID
    ]


# =========================================================
# DUPLICATE FILTER
# =========================================================

def canonicalize_name(
    name: str,
) -> str:

    return (
        cached_normalize(name)
        .replace("assessment", "")
        .replace("adaptive", "")
        .replace("simulation", "")
        .replace("(new)", "")
        .replace("2.0", "")
        .replace("1.0", "")
        .strip()
    )


def is_duplicate_result(
    item: dict[str, Any],
    existing: list[dict[str, Any]],
) -> bool:

    current = canonicalize_name(
        item.get("name", "")
    )

    for existing_item in existing:

        existing_name = canonicalize_name(
            existing_item.get(
                "name",
                ""
            )
        )

        if current == existing_name:
            return True

    return False


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

    confidence = (
        0.40
        + (
            math.sqrt(score)
            * 0.58
        )
    )

    return round(
        min(confidence, 0.99),
        2,
    )


# =========================================================
# EXPLANATION
# =========================================================

def build_explanation(
    item: dict[str, Any],
    query: str,
) -> str:

    searchable = build_document_text(
        item
    )

    query_norm = cached_normalize(
        query
    )

    reasons: list[str] = []

    if any(
        term in query_norm
        for term in TECH_KEYWORDS
    ):

        if any(
            term in searchable
            for term in TECH_KEYWORDS
        ):

            reasons.append(
                "strong technical skill alignment"
            )

    if any(
        term in query_norm
        for term in DATA_KEYWORDS
    ):

        reasons.append(
            "data science capability matching"
        )

    if any(
        term in query_norm
        for term in LEADERSHIP_KEYWORDS
    ):

        reasons.append(
            "leadership competency coverage"
        )

    if any(
        term in query_norm
        for term in COMMUNICATION_KEYWORDS
    ):

        reasons.append(
            "communication competency matching"
        )

    if not reasons:

        reasons.append(
            "high semantic relevance"
        )

    return (
        "Recommended because of "
        + ", ".join(reasons)
        + "."
    )


# =========================================================
# MAIN SEARCH
# =========================================================

def search_assessments(
    query: str,
) -> list[dict[str, Any]]:

    try:

        if not query:
            return []

        query = cached_normalize(
            query
        )

        if not query.strip():
            return []

        expanded_query = expand_query(
            query
        )

        logger.info(
            "Original query=%s",
            query,
        )

        logger.info(
            "Expanded query=%s",
            expanded_query,
        )

        # ============================================
        # RETRIEVAL
        # ============================================

        semantic_results = semantic_search(
            expanded_query
        )

        bm25_results = bm25_search(
            expanded_query
        )

        # ============================================
        # HYBRID FUSION
        # ============================================

        fused_results = hybrid_fusion(
            query,
            semantic_results,
            bm25_results,
        )

        final_results = []

        type_counts = defaultdict(int)

        for idx, score in fused_results:

            if (
                score
                < MIN_ACCEPTABLE_SCORE
            ):
                continue

            item = CATALOG[idx]

            test_type = str(
                item.get(
                    "test_type",
                    "K",
                )
            ).upper()

            if (
                test_type
                not in VALID_TEST_TYPES
            ):
                continue

            # ========================================
            # DIVERSITY CONTROL
            # ========================================

            if (
                type_counts[test_type]
                >= MAX_SAME_TYPE_RESULTS
            ):
                continue

            # ========================================
            # DUPLICATE CONTROL
            # ========================================

            if is_duplicate_result(
                item,
                final_results,
            ):
                continue

            confidence = (
                compute_confidence(
                    score
                )
            )

            recommendation_strength = (
                "high"
                if confidence
                >= HIGH_CONFIDENCE_THRESHOLD
                else (
                    "medium"
                    if confidence >= 0.68
                    else "low"
                )
            )

            result = {

                "name":
                    item.get("name"),

                "url":
                    item.get("url"),

                "test_type":
                    test_type,

                "description":
                    item.get(
                        "description",
                        "",
                    ),

                "score":
                    round(score, 4),

                "confidence":
                    confidence,

                "recommendation_strength":
                    recommendation_strength,

                "roles":
                    item.get(
                        "roles",
                        [],
                    ),

                "domains":
                    item.get(
                        "domains",
                        [],
                    ),

                "skills":
                    item.get(
                        "technical_skills",
                        [],
                    ),

                "explanation":
                    build_explanation(
                        item,
                        query,
                    ),
            }

            final_results.append(
                result
            )

            type_counts[
                test_type
            ] += 1

            if (
                len(final_results)
                >= FINAL_RECOMMENDATIONS
            ):
                break

        logger.info(
            "Final recommendations=%s",
            [
                (
                    item["name"],
                    item["score"],
                )
                for item in final_results
            ],
        )

        return final_results

    except Exception as error:

        logger.exception(
            "Retrieval failed: %s",
            error,
        )

        return []