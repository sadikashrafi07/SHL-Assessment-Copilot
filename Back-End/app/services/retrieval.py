# =========================================================
# app/services/retrieval.py
# Production-Grade Hybrid Retrieval Engine
# =========================================================

from __future__ import annotations

import json
import logging
import os

from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from fastembed import TextEmbedding
from rank_bm25 import BM25Okapi

from app.config.settings import (
    ENABLE_BM25,
    FINAL_RECOMMENDATIONS,
    HIGH_CONFIDENCE_THRESHOLD,
    MAX_SAME_TYPE_RESULTS,
    MIN_ACCEPTABLE_SCORE,
    MIN_SIMILARITY_THRESHOLD,
    QUERY_EXPANSIONS,
    ROLE_COMPETENCIES,
    TOP_K_BM25,
    TOP_K_HYBRID,
    TOP_K_SEMANTIC,
    VALID_TEST_TYPES,
)

from app.utils.helpers import normalize

# =========================================================
# ENV
# =========================================================

os.environ["TOKENIZERS_PARALLELISM"] = "false"

logger = logging.getLogger(__name__)

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

CATALOG_PATH = DATA_DIR / "cleaned_catalog.json"

EMBEDDINGS_PATH = (
    DATA_DIR / "catalog_embeddings.npy"
)

# =========================================================
# LOAD CATALOG
# =========================================================


def load_catalog() -> list[dict[str, Any]]:

    with open(
        CATALOG_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    return data


CATALOG = load_catalog()

# =========================================================
# EMBEDDINGS
# =========================================================


@lru_cache(maxsize=1)
def get_catalog_embeddings():

    return np.load(
        EMBEDDINGS_PATH,
        mmap_mode="r",
    ).astype(np.float32)


@lru_cache(maxsize=1)
def get_embedding_model():

    return TextEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )


# =========================================================
# DOCUMENTS
# =========================================================


def build_document_text(
    item: dict[str, Any],
) -> str:

    sections = [

        item.get("name", ""),

        item.get("description", ""),

        " ".join(item.get("roles", [])),

        " ".join(item.get("domains", [])),

        " ".join(
            item.get(
                "technical_skills",
                [],
            )
        ),

        " ".join(
            item.get(
                "expanded_competencies",
                [],
            )
        ),

        " ".join(
            item.get(
                "leadership_traits",
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
                "cognitive_traits",
                [],
            )
        ),

        " ".join(
            item.get(
                "personality_traits",
                [],
            )
        ),
    ]

    return normalize(
        " ".join(
            x for x in sections if x
        )
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

    query = normalize(query)

    expansions = []

    for trigger, terms in (
        QUERY_EXPANSIONS.items()
    ):

        if trigger in query:
            expansions.extend(terms)

    for role, terms in (
        ROLE_COMPETENCIES.items()
    ):

        if role in query:
            expansions.extend(terms)

    expansions = list(set(expansions))

    expanded_query = (
        query
        + " "
        + " ".join(expansions)
    )

    return normalize(expanded_query)


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

    norm = np.linalg.norm(
        embedding
    )

    if norm > 0:
        embedding = embedding / norm

    return embedding


# =========================================================
# BM25 SEARCH
# =========================================================


def bm25_search(
    query: str,
    top_k: int = TOP_K_BM25,
):

    if not ENABLE_BM25:
        return []

    scores = BM25.get_scores(
        query.split()
    )

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True,
    )

    max_score = max(scores) if len(scores) else 1.0

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

        results.append(
            (
                int(idx),
                round(
                    float(similarities[idx]),
                    4,
                ),
            )
        )

    return results


# =========================================================
# ROLE SCORE
# =========================================================


def role_match_score(
    query: str,
    item: dict[str, Any],
) -> float:

    query = normalize(query)

    roles = item.get(
        "roles",
        [],
    )

    if not roles:
        return 0.0

    best = 0.0

    for role in roles:

        role = normalize(role)

        if role in query:
            best = max(best, 1.0)

        role_tokens = set(role.split())

        query_tokens = set(
            query.split()
        )

        overlap = len(
            role_tokens
            & query_tokens
        )

        score = overlap / max(
            len(role_tokens),
            1,
        )

        best = max(best, score)

    return round(best, 4)


# =========================================================
# SKILL SCORE
# =========================================================


def skill_match_score(
    query: str,
    item: dict[str, Any],
) -> float:

    query = normalize(query)

    skills = []

    skills.extend(
        item.get(
            "technical_skills",
            [],
        )
    )

    skills.extend(
        item.get(
            "expanded_competencies",
            [],
        )
    )

    if not skills:
        return 0.0

    matches = 0

    for skill in skills:

        if normalize(skill) in query:
            matches += 1

    return min(
        matches * 0.12,
        1.0,
    )


# =========================================================
# DOMAIN BOOST
# =========================================================


def ontology_boost(
    query: str,
    item: dict[str, Any],
) -> float:

    query = normalize(query)

    boost = 0.0

    domains = item.get(
        "domains",
        [],
    )

    test_type = item.get(
        "test_type",
        "K",
    )

    if (
        "python" in query
        or "java" in query
        or "developer" in query
        or "software engineer" in query
    ):

        if "technical" in domains:
            boost += 0.20

    if "leadership" in query:

        if (
            "leadership"
            in domains
        ):
            boost += 0.15

        if test_type == "L":
            boost += 0.10

    if "communication" in query:

        if (
            "communication"
            in domains
        ):
            boost += 0.10

    return min(boost, 0.30)


# =========================================================
# DIVERSITY
# =========================================================


def is_duplicate_result(
    item: dict[str, Any],
    existing: list[dict[str, Any]],
) -> bool:

    current_name = normalize(
        item.get("name", "")
    )

    for existing_item in existing:

        existing_name = normalize(
            existing_item.get(
                "name",
                "",
            )
        )

        if current_name == existing_name:
            return True

    return False


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

    all_doc_ids = set(
        semantic_map.keys()
    ) | set(
        bm25_map.keys()
    )

    fused = []

    for doc_id in all_doc_ids:

        item = CATALOG[doc_id]

        semantic_score = (
            semantic_map.get(
                doc_id,
                0.0,
            )
        )

        bm25_score = (
            bm25_map.get(
                doc_id,
                0.0,
            )
        )

        role_score = (
            role_match_score(
                query,
                item,
            )
        )

        skill_score = (
            skill_match_score(
                query,
                item,
            )
        )

        boost = ontology_boost(
            query,
            item,
        )

        final_score = (

            semantic_score * 0.40

            +

            bm25_score * 0.30

            +

            role_score * 0.20

            +

            skill_score * 0.10

            +

            boost
        )

        fused.append(
            (
                doc_id,
                round(
                    final_score,
                    4,
                ),
            )
        )

    fused.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    return fused[:TOP_K_HYBRID]


# =========================================================
# MAIN SEARCH
# =========================================================


def search_assessments(
    query: str,
) -> list[dict[str, Any]]:

    try:

        if not query.strip():
            return []

        semantic_query = normalize(
            query
        )

        bm25_query = expand_query(
            query
        )

        logger.info(
            "Semantic Query: %s",
            semantic_query,
        )

        logger.info(
            "Expanded Query: %s",
            bm25_query,
        )

        semantic_results = (
            semantic_search(
                semantic_query
            )
        )

        bm25_results = (
            bm25_search(
                bm25_query
            )
        )

        fused_results = (
            hybrid_fusion(
                query,
                semantic_results,
                bm25_results,
            )
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

            test_type = item.get(
                "test_type",
                "K",
            )

            if (
                test_type
                not in VALID_TEST_TYPES
            ):
                continue

            if (
                type_counts[test_type]
                >= MAX_SAME_TYPE_RESULTS
            ):
                continue

            if is_duplicate_result(
                item,
                final_results,
            ):
                continue

            confidence = min(
                round(score, 2),
                0.99,
            )

            strength = (
                "high"
                if confidence >= 0.85
                else (
                    "medium"
                    if confidence >= 0.65
                    else "low"
                )
            )

            result = {
                "name": item.get(
                    "name"
                ),
                "url": item.get(
                    "url"
                ),
                "test_type": test_type,
                "description": item.get(
                    "description",
                    "",
                ),
                "score": round(
                    score,
                    4,
                ),
                "confidence": confidence,
                "recommendation_strength":
                    strength,
                "explanation":
                    item.get(
                        "explanation",
                        "",
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
            "Returning %s recommendations",
            len(final_results),
        )

        return final_results

    except Exception as e:

        logger.exception(
            "Retrieval failed: %s",
            e,
        )

        return []