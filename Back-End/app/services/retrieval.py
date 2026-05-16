# =========================================================
# app/services/retrieval.py
# Production-Grade Hybrid Retrieval Engine
# =========================================================

from __future__ import annotations

import json
import logging
import math
import os
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from sentence_transformers import SentenceTransformer

from app.config.settings import (
    BM25_WEIGHT,
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_PATH,
    CROSS_ENCODER_MODEL,
    CROSS_ENCODER_WEIGHT,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL,
    EMBEDDING_NORMALIZE,
    ENABLE_BM25,
    ENABLE_CROSS_ENCODER,
    ENABLE_HYBRID_RETRIEVAL,
    FINAL_RECOMMENDATIONS,
    HIGH_CONFIDENCE_THRESHOLD,
    KEYWORD_WEIGHT,
    MAX_SAME_TYPE_RESULTS,
    MIN_ACCEPTABLE_SCORE,
    MIN_SIMILARITY_THRESHOLD,
    QUERY_EXPANSIONS,
    ROLE_COMPETENCIES,
    ROLE_WEIGHT,
    SEMANTIC_WEIGHT,
    SOFT_SKILL_WEIGHT,
    TOP_K_BM25,
    TOP_K_HYBRID,
    TOP_K_RERANK,
    TOP_K_SEMANTIC,
    VALID_TEST_TYPES,
)

from app.utils.helpers import normalize

logger = logging.getLogger(__name__)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

CATALOG_PATH = DATA_DIR / "cleaned_catalog.json"

# =========================================================
# LOAD CATALOG
# =========================================================


def load_catalog() -> list[dict[str, Any]]:

    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Missing catalog file: {CATALOG_PATH}"
        )

    with open(
        CATALOG_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            "Catalog must contain a list"
        )

    return data


CATALOG = load_catalog()

# =========================================================
# MODELS
# =========================================================


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:

    logger.info(
        "Loading embedding model..."
    )

    return SentenceTransformer(
        EMBEDDING_MODEL
    )


@lru_cache(maxsize=1)
def get_cross_encoder() -> CrossEncoder:

    logger.info(
        "Loading cross encoder..."
    )

    return CrossEncoder(
        CROSS_ENCODER_MODEL
    )


# =========================================================
# CHROMA
# =========================================================

client = chromadb.PersistentClient(
    path=CHROMA_DB_PATH,
    settings=chromadb.Settings(
        anonymized_telemetry=False
    ),
)

collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={
        "hnsw:space": "cosine"
    },
)

# =========================================================
# DOCUMENT BUILDING
# =========================================================


def build_document_text(
    item: dict[str, Any]
) -> str:

    weighted_sections = [
        item.get("name", ""),
        item.get("name", ""),
        item.get("description", ""),
        item.get("dense_text", ""),
        item.get("sparse_text", ""),
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
        " ".join(
            item.get(
                "expanded_competencies",
                [],
            )
        ),
        " ".join(
            item.get(
                "intents",
                [],
            )
        ),
    ]

    return normalize(
        " ".join(
            part
            for part in weighted_sections
            if part
        )
    )


DOCUMENTS = [
    build_document_text(item)
    for item in CATALOG
]

TOKENIZED_CORPUS = [
    doc.split()
    for doc in DOCUMENTS
]

BM25 = BM25Okapi(
    TOKENIZED_CORPUS
)

# =========================================================
# CHROMA INITIALIZATION
# =========================================================


def initialize_chroma() -> None:

    try:

        existing_count = collection.count()

        if existing_count > 0:

            logger.info(
                "Chroma already initialized"
            )

            return

        model = get_embedding_model()

        logger.info(
            "Generating embeddings..."
        )

        embeddings = model.encode(
            DOCUMENTS,
            normalize_embeddings=EMBEDDING_NORMALIZE,
            batch_size=EMBEDDING_BATCH_SIZE,
            show_progress_bar=True,
        )

        ids = []
        metadatas = []

        for idx, item in enumerate(CATALOG):

            ids.append(str(idx))

            metadata = {
                "name": item.get(
                    "name",
                    "",
                ),
                "url": item.get(
                    "url",
                    "",
                ),
                "description": item.get(
                    "description",
                    "",
                ),
                "test_type": item.get(
                    "test_type",
                    "K",
                ),
                "roles": ",".join(
                    item.get(
                        "roles",
                        [],
                    )
                ),
                "domains": ",".join(
                    item.get(
                        "domains",
                        [],
                    )
                ),
            }

            metadatas.append(metadata)

        collection.add(
            ids=ids,
            documents=DOCUMENTS,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
        )

        logger.info(
            "Indexed %s assessments",
            len(CATALOG),
        )

    except Exception as e:

        logger.exception(
            "Chroma initialization failed: %s",
            e,
        )


# =========================================================
# QUERY EXPANSION
# =========================================================


def expand_query(
    query: str
) -> str:

    normalized_query = normalize(query)

    expansions = set()

    for trigger, terms in (
        QUERY_EXPANSIONS.items()
    ):

        if trigger in normalized_query:
            expansions.update(terms)

    for role, competencies in (
        ROLE_COMPETENCIES.items()
    ):

        if role in normalized_query:
            expansions.update(
                competencies
            )

    expanded_query = (
        normalized_query
        + " "
        + " ".join(expansions)
    )

    return normalize(
        expanded_query
    )


# =========================================================
# BM25 SEARCH
# =========================================================


def bm25_search(
    query: str,
    top_k: int = TOP_K_BM25,
) -> list[tuple[int, float]]:

    if not ENABLE_BM25:
        return []

    tokenized_query = query.split()

    scores = BM25.get_scores(
        tokenized_query
    )

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True,
    )

    max_score = (
        max(scores)
        if len(scores) > 0
        else 1
    )

    normalized_results = []

    for idx, score in ranked[:top_k]:

        normalized_score = (
            float(score) / max_score
            if max_score > 0
            else 0.0
        )

        normalized_results.append(
            (
                idx,
                round(
                    normalized_score,
                    4,
                ),
            )
        )

    return normalized_results


# =========================================================
# SEMANTIC SEARCH
# =========================================================


def semantic_search(
    query: str,
    top_k: int = TOP_K_SEMANTIC,
) -> list[tuple[int, float]]:

    model = get_embedding_model()

    embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    response = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
    )

    ids = response["ids"][0]

    distances = response["distances"][0]

    results = []

    for idx, distance in zip(
        ids,
        distances,
    ):

        similarity = max(
            0.0,
            1.0
            - (
                float(distance)
                / 2.0
            ),
        )

        results.append(
            (
                int(idx),
                round(
                    similarity,
                    4,
                ),
            )
        )

    return results


# =========================================================
# ROLE MATCH SCORING
# =========================================================


def role_match_score(
    query: str,
    item: dict[str, Any],
) -> float:

    query = normalize(query)

    roles = [
        normalize(role)
        for role in item.get(
            "roles",
            [],
        )
    ]

    if not roles:
        return 0.0

    score = 0.0

    for role in roles:

        if role in query:
            score += 1.0

        role_parts = role.split()

        partial_matches = sum(
            1
            for word in role_parts
            if word in query
        )

        score += (
            partial_matches
            / max(
                len(role_parts),
                1,
            )
        ) * 0.5

    return min(score, 1.0)


# =========================================================
# SOFT SKILL MATCHING
# =========================================================


def soft_skill_score(
    query: str,
    item: dict[str, Any],
) -> float:

    query = normalize(query)

    skills = []

    skills.extend(
        item.get(
            "communication_skills",
            [],
        )
    )

    skills.extend(
        item.get(
            "leadership_traits",
            [],
        )
    )

    skills.extend(
        item.get(
            "personality_traits",
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
        matches / len(skills),
        1.0,
    )


# =========================================================
# HYBRID FUSION
# =========================================================


def hybrid_fusion(
    query: str,
    bm25_results: list[
        tuple[int, float]
    ],
    semantic_results: list[
        tuple[int, float]
    ],
) -> list[tuple[int, float]]:

    combined_scores = defaultdict(float)

    bm25_map = dict(bm25_results)

    semantic_map = dict(
        semantic_results
    )

    all_doc_ids = set(
        bm25_map.keys()
    ) | set(
        semantic_map.keys()
    )

    for doc_id in all_doc_ids:

        bm25_score = bm25_map.get(
            doc_id,
            0.0,
        )

        semantic_score = semantic_map.get(
            doc_id,
            0.0,
        )

        item = CATALOG[doc_id]

        role_score = role_match_score(
            query,
            item,
        )

        skill_score = soft_skill_score(
            query,
            item,
        )

        final_score = (
            semantic_score
            * SEMANTIC_WEIGHT
            + bm25_score
            * KEYWORD_WEIGHT
            + role_score
            * ROLE_WEIGHT
            + skill_score
            * SOFT_SKILL_WEIGHT
        )

        combined_scores[
            doc_id
        ] = final_score

    ranked = sorted(
        combined_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return ranked[:TOP_K_HYBRID]


# =========================================================
# ONTOLOGY BOOSTING
# =========================================================


def ontology_boost(
    query: str,
    item: dict[str, Any],
) -> float:

    boost = 0.0

    query = normalize(query)

    domains = item.get(
        "domains",
        [],
    )

    competencies = item.get(
        "expanded_competencies",
        [],
    )

    test_type = item.get(
        "test_type",
        "K",
    )

    if "leadership" in query:

        if "leadership" in domains:
            boost += 0.10

        if test_type == "L":
            boost += 0.08

    if "communication" in query:

        if "communication" in domains:
            boost += 0.08

    if (
        "software engineer"
        in query
        or "developer" in query
    ):

        if "technical" in domains:
            boost += 0.12

    if (
        "data scientist"
        in query
        or "data analyst"
        in query
    ):

        if "cognitive" in domains:
            boost += 0.10

    if (
        "devops"
        in query
        or "cloud" in query
    ):

        if "technical" in domains:
            boost += 0.12

    competency_hits = 0

    for competency in competencies:

        if competency in query:
            competency_hits += 1

    boost += min(
        competency_hits * 0.02,
        0.10,
    )

    return min(boost, 0.25)


# =========================================================
# CROSS ENCODER RERANKING
# =========================================================


def rerank_results(
    query: str,
    candidates: list[
        tuple[int, float]
    ],
) -> list[tuple[int, float]]:

    if (
        not ENABLE_CROSS_ENCODER
        or not candidates
    ):
        return candidates

    try:

        cross_encoder = (
            get_cross_encoder()
        )

        pairs = []

        for idx, _ in candidates:

            pairs.append(
                (
                    query,
                    DOCUMENTS[idx],
                )
            )

        cross_scores = (
            cross_encoder.predict(
                pairs
            )
        )

        reranked = []

        for (
            (idx, base_score),
            ce_score,
        ) in zip(
            candidates,
            cross_scores,
        ):

            normalized_ce_score = (
                1
                / (
                    1
                    + math.exp(
                        -float(
                            ce_score
                        )
                    )
                )
            )

            final_score = (
                base_score
                * (
                    1
                    - CROSS_ENCODER_WEIGHT
                )
                + normalized_ce_score
                * CROSS_ENCODER_WEIGHT
            )

            reranked.append(
                (
                    idx,
                    round(
                        final_score,
                        4,
                    ),
                )
            )

        reranked.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        return reranked[
            :TOP_K_RERANK
        ]

    except Exception as e:

        logger.exception(
            "Cross encoder reranking failed: %s",
            e,
        )

        return candidates


# =========================================================
# MAIN SEARCH FUNCTION
# =========================================================


def search_assessments(
    query: str,
) -> list[dict[str, Any]]:

    if not query.strip():
        return []

    try:

        expanded_query = expand_query(
            query
        )

        logger.info(
            "Expanded query: %s",
            expanded_query,
        )

        bm25_results = bm25_search(
            expanded_query
        )

        semantic_results = (
            semantic_search(
                expanded_query
            )
        )

        fused_results = hybrid_fusion(
            expanded_query,
            bm25_results,
            semantic_results,
        )

        reranked_results = (
            rerank_results(
                expanded_query,
                fused_results,
            )
        )

        final_results = []

        seen_names = set()

        type_counts = defaultdict(int)

        for (
            idx,
            score,
        ) in reranked_results:

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

            normalized_name = (
                normalize(
                    item["name"]
                )
            )

            if (
                normalized_name
                in seen_names
            ):
                continue

            seen_names.add(
                normalized_name
            )

            boosted_score = min(
                score
                + ontology_boost(
                    expanded_query,
                    item,
                ),
                1.0,
            )

            if (
                boosted_score
                < MIN_SIMILARITY_THRESHOLD
            ):
                continue

            type_counts[
                test_type
            ] += 1

            recommendation_strength = (
                "high"
                if boosted_score
                >= HIGH_CONFIDENCE_THRESHOLD
                else (
                    "medium"
                    if boosted_score
                    >= 0.55
                    else "low"
                )
            )

            explanation = (
                f"This assessment matches "
                f"the role requirements for "
                f"{query} and evaluates "
                f"relevant competencies such as "
                f"{', '.join(item.get('expanded_competencies', [])[:5])}."
            )

            final_results.append(
                {
                    "name": item[
                        "name"
                    ],
                    "url": item[
                        "url"
                    ],
                    "description": item.get(
                        "description",
                        "",
                    ),
                    "test_type": test_type,
                    "score": round(
                        boosted_score,
                        4,
                    ),
                    "confidence": round(
                        boosted_score,
                        2,
                    ),
                    "recommendation_strength": recommendation_strength,
                    "high_confidence": (
                        boosted_score
                        >= HIGH_CONFIDENCE_THRESHOLD
                    ),
                    "roles": item.get(
                        "roles",
                        [],
                    ),
                    "domains": item.get(
                        "domains",
                        [],
                    ),
                    "explanation": explanation,
                }
            )

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
            "Assessment retrieval failed: %s",
            e,
        )

        return []


# =========================================================
# AUTO INITIALIZATION
# =========================================================

initialize_chroma()