# =========================================================
# app/services/query_expander.py
# Enterprise-Grade Semantic Query Expansion Engine
# =========================================================

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any, Dict, List, Set, Tuple

from app.config.settings import (
    ENABLE_QUERY_EXPANSION,
    MAX_EXPANSION_TERMS,
)

from app.utils.helpers import normalize

logger = logging.getLogger(__name__)

# =========================================================
# CONSTANTS
# =========================================================

DEFAULT_WEIGHT = 1.0

GENERAL_CONTEXT = "general"

# =========================================================
# QUERY EXPANSIONS
# =========================================================

QUERY_EXPANSIONS: Dict[
    str,
    Dict[str, List[Tuple[str, float]]],
] = {
    "python": {
        "general": [
            ("programming", 0.90),
            ("software engineer", 0.85),
            ("automation", 0.75),
        ],
        "backend": [
            ("django", 0.95),
            ("flask", 0.92),
            ("fastapi", 0.95),
            ("backend", 0.85),
            ("api", 0.80),
        ],
        "data": [
            ("machine learning", 0.92),
            ("data science", 0.88),
            ("analytics", 0.75),
            ("ai", 0.85),
        ],
    },

    "java": {
        "general": [
            ("programming", 0.85),
            ("software engineer", 0.90),
        ],
        "backend": [
            ("spring", 0.95),
            ("spring boot", 0.95),
            ("microservices", 0.85),
            ("backend", 0.80),
        ],
    },

    "javascript": {
        "frontend": [
            ("react", 0.95),
            ("frontend", 0.90),
            ("web development", 0.82),
        ],
        "backend": [
            ("node", 0.90),
            ("nodejs", 0.90),
            ("api", 0.75),
        ],
    },

    "typescript": {
        "frontend": [
            ("react", 0.92),
            ("angular", 0.88),
            ("frontend", 0.90),
        ],
        "backend": [
            ("nodejs", 0.90),
            ("backend", 0.82),
        ],
    },

    "react": {
        "frontend": [
            ("javascript", 0.90),
            ("typescript", 0.88),
            ("frontend", 0.95),
            ("ui", 0.82),
        ]
    },

    "cloud": {
        "general": [
            ("aws", 0.95),
            ("azure", 0.95),
            ("gcp", 0.92),
            ("infrastructure", 0.75),
        ],
        "devops": [
            ("docker", 0.95),
            ("kubernetes", 0.95),
            ("devops", 0.90),
            ("deployment", 0.75),
        ],
    },

    "devops": {
        "general": [
            ("docker", 0.95),
            ("kubernetes", 0.95),
            ("jenkins", 0.85),
            ("ci/cd", 0.82),
            ("deployment", 0.75),
        ]
    },

    "communication": {
        "general": [
            ("stakeholder", 0.92),
            ("presentation", 0.92),
            ("collaboration", 0.85),
            ("client communication", 0.85),
            ("verbal", 0.75),
        ]
    },

    "personality": {
        "general": [
            ("behavioral", 0.92),
            ("behavior", 0.85),
            ("culture fit", 0.82),
            ("motivation", 0.75),
            ("traits", 0.72),
            ("opq", 0.92),
        ]
    },

    "leadership": {
        "general": [
            ("management", 0.92),
            ("decision making", 0.85),
            ("ownership", 0.80),
            ("strategic thinking", 0.82),
            ("team leadership", 0.82),
        ]
    },

    "cognitive": {
        "general": [
            ("reasoning", 0.92),
            ("aptitude", 0.92),
            ("logical thinking", 0.85),
            ("problem solving", 0.85),
            ("analytical", 0.82),
        ]
    },

    "junior": {
        "general": [
            ("entry level", 0.90),
            ("graduate", 0.82),
            ("associate", 0.72),
        ]
    },

    "senior": {
        "general": [
            ("lead", 0.90),
            ("principal", 0.85),
            ("architect", 0.85),
        ]
    },

    "product manager": {
        "general": [
            ("stakeholder management", 0.95),
            ("roadmapping", 0.90),
            ("strategy", 0.90),
            ("leadership", 0.85),
            ("communication", 0.82),
        ]
    },

    "software engineer": {
        "general": [
            ("coding", 0.95),
            ("algorithms", 0.90),
            ("problem solving", 0.90),
            ("technical assessment", 0.88),
        ]
    },
}

# =========================================================
# CONTEXT TERMS
# =========================================================

CONTEXT_TERMS: Dict[str, Set[str]] = {
    "backend": {
        "backend",
        "api",
        "microservices",
        "server",
        "spring",
        "fastapi",
        "django",
        "flask",
    },

    "frontend": {
        "frontend",
        "ui",
        "react",
        "angular",
        "web",
        "javascript",
        "typescript",
    },

    "data": {
        "data",
        "analytics",
        "machine learning",
        "ai",
        "statistics",
    },

    "devops": {
        "devops",
        "docker",
        "kubernetes",
        "cloud",
        "aws",
        "azure",
        "gcp",
    },
}

# =========================================================
# COMPARISON TERMS
# =========================================================

COMPARISON_TERMS: Set[str] = {
    "compare",
    "comparison",
    "difference",
    "vs",
    "versus",
    "better than",
    "alternative to",
}

# =========================================================
# PHRASES
# =========================================================

MULTI_WORD_PHRASES: List[str] = [
    "software engineer",
    "software developer",
    "cloud engineer",
    "data engineer",
    "machine learning",
    "full stack",
    "frontend developer",
    "backend developer",
    "critical thinking",
    "problem solving",
    "product manager",
    "data scientist",
    "stakeholder management",
]

# =========================================================
# REGEX HELPERS
# =========================================================

@lru_cache(maxsize=4096)
def build_word_pattern(
    term: str,
) -> re.Pattern:
    """
    Cached whole-word regex pattern.
    """

    normalized_term = normalize(term)

    return re.compile(
        rf"\b{re.escape(normalized_term)}\b",
        flags=re.IGNORECASE,
    )


def regex_match(
    term: str,
    text: str,
) -> bool:
    """
    Safe regex matching.
    """

    if not term or not text:
        return False

    return bool(
        build_word_pattern(term).search(
            normalize(text)
        )
    )

# =========================================================
# QUERY TYPE DETECTION
# =========================================================

def is_comparison_query(
    query: str,
) -> bool:
    """
    Detect comparison-oriented queries.
    """

    normalized_query = normalize(query)

    return any(
        regex_match(term, normalized_query)
        for term in COMPARISON_TERMS
    )

# =========================================================
# TOKENIZER
# =========================================================

def tokenize_query(
    query: str,
) -> List[str]:
    """
    Phrase-aware tokenizer.
    """

    if not query:
        return []

    normalized_query = normalize(query)

    detected_phrases: List[str] = []

    # =====================================================
    # PHRASE PRESERVATION
    # =====================================================

    for phrase in MULTI_WORD_PHRASES:

        if regex_match(
            phrase,
            normalized_query,
        ):

            detected_phrases.append(
                normalize(phrase)
            )

            normalized_query = re.sub(
                build_word_pattern(phrase),
                phrase.replace(" ", "_"),
                normalized_query,
            )

    # =====================================================
    # TOKEN EXTRACTION
    # =====================================================

    raw_tokens = re.findall(
        r"\b[\w\-/]+\b",
        normalized_query,
    )

    tokens: List[str] = []

    for token in raw_tokens:

        cleaned = normalize(
            token.replace("_", " ")
        )

        if cleaned:
            tokens.append(cleaned)

    # =====================================================
    # ADD PHRASES BACK
    # =====================================================

    tokens.extend(detected_phrases)

    # =====================================================
    # DEDUPLICATION
    # =====================================================

    unique_tokens = list(
        dict.fromkeys(tokens)
    )

    return unique_tokens

# =========================================================
# CONTEXT DETECTION
# =========================================================

def detect_query_context(
    tokens: List[str],
) -> List[str]:
    """
    Detect semantic contexts.
    """

    contexts: Set[str] = set()

    for token in tokens:

        normalized_token = normalize(
            token
        )

        for (
            context,
            keywords,
        ) in CONTEXT_TERMS.items():

            if normalized_token in keywords:
                contexts.add(context)

    if not contexts:
        contexts.add(GENERAL_CONTEXT)

    return sorted(contexts)

# =========================================================
# TERM COMPRESSION
# =========================================================

def compress_terms(
    weighted_terms: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Keep highest-weight term occurrence.
    """

    compressed: Dict[
        str,
        Dict[str, Any],
    ] = {}

    for item in weighted_terms:

        term = normalize(
            item.get("term", "")
        )

        if not term:
            continue

        existing = compressed.get(term)

        if (
            existing is None
            or item["weight"]
            > existing["weight"]
        ):
            compressed[term] = item

    final_terms = sorted(
        compressed.values(),
        key=lambda x: (
            x["weight"],
            x["term"],
        ),
        reverse=True,
    )

    return final_terms

# =========================================================
# CORE EXPANSION ENGINE
# =========================================================

def _build_weighted_terms(
    query: str,
) -> List[Dict[str, Any]]:
    """
    Internal semantic expansion engine.
    """

    if not query:
        return []

    if not ENABLE_QUERY_EXPANSION:
        return [
            {
                "term": normalize(query),
                "weight": 1.0,
                "source": "disabled",
                "context": "disabled",
            }
        ]

    normalized_query = normalize(query)

    # =====================================================
    # COMPARISON QUERIES
    # =====================================================

    if is_comparison_query(
        normalized_query
    ):
        return [
            {
                "term": normalized_query,
                "weight": 1.0,
                "source": "comparison_query",
                "context": "comparison",
            }
        ]

    # =====================================================
    # TOKENIZATION
    # =====================================================

    tokens = tokenize_query(
        normalized_query
    )

    contexts = detect_query_context(
        tokens
    )

    weighted_terms: List[
        Dict[str, Any]
    ] = []

    seen: Set[str] = set()

    # =====================================================
    # ORIGINAL TOKENS
    # =====================================================

    for token in tokens:

        normalized_token = normalize(
            token
        )

        if (
            not normalized_token
            or normalized_token in seen
        ):
            continue

        weighted_terms.append(
            {
                "term": normalized_token,
                "weight": DEFAULT_WEIGHT,
                "source": "original",
                "context": "primary",
            }
        )

        seen.add(normalized_token)

    # =====================================================
    # SEMANTIC EXPANSIONS
    # =====================================================

    for token in tokens:

        normalized_token = normalize(
            token
        )

        expansion_map = (
            QUERY_EXPANSIONS.get(
                normalized_token
            )
        )

        if not expansion_map:
            continue

        applicable_contexts = list(
            dict.fromkeys(
                contexts
                + [GENERAL_CONTEXT]
            )
        )

        for context in applicable_contexts:

            expansions = expansion_map.get(
                context,
                [],
            )

            for (
                related_term,
                weight,
            ) in expansions:

                normalized_term = normalize(
                    related_term
                )

                if (
                    not normalized_term
                    or normalized_term in seen
                ):
                    continue

                validated_weight = max(
                    0.0,
                    min(float(weight), 1.0),
                )

                if context == GENERAL_CONTEXT:
                    validated_weight = round(
                        validated_weight * 0.9,
                        3,
                    )
                else:
                    validated_weight = round(
                        validated_weight,
                        3,
                    )

                weighted_terms.append(
                    {
                        "term": normalized_term,
                        "weight": validated_weight,
                        "source": normalized_token,
                        "context": context,
                    }
                )

                seen.add(normalized_term)

    # =====================================================
    # COMPRESS + LIMIT
    # =====================================================

    compressed = compress_terms(
        weighted_terms
    )

    return compressed[
        :MAX_EXPANSION_TERMS
    ]

# =========================================================
# PUBLIC API
# =========================================================

def expand_query(
    query: str,
) -> str:
    """
    Expand query into semantic text.
    """

    weighted_terms = (
        _build_weighted_terms(query)
    )

    expanded_query = " ".join(
        item["term"]
        for item in weighted_terms
    )

    logger.info(
        "Expanded query=%s",
        expanded_query,
    )

    return expanded_query


def expand_query_with_weights(
    query: str,
) -> List[Dict[str, Any]]:
    """
    Return weighted semantic terms.
    """

    weighted_terms = (
        _build_weighted_terms(query)
    )

    logger.info(
        "Expansion term count=%s",
        len(weighted_terms),
    )

    return weighted_terms


def build_expansion_metadata(
    query: str,
) -> Dict[str, Any]:
    """
    Build structured expansion metadata.
    """

    normalized_query = normalize(
        query
    )

    tokens = tokenize_query(
        normalized_query
    )

    contexts = detect_query_context(
        tokens
    )

    weighted_terms = (
        expand_query_with_weights(
            normalized_query
        )
    )

    expanded_query = " ".join(
        item["term"]
        for item in weighted_terms
    )

    metadata = {
        "original_query":
            normalized_query,

        "expanded_query":
            expanded_query,

        "weighted_terms":
            weighted_terms,

        "token_count":
            len(tokens),

        "expansion_term_count":
            len(weighted_terms),

        "contexts":
            contexts,

        "comparison_query":
            is_comparison_query(
                normalized_query
            ),

        "expansion_enabled":
            ENABLE_QUERY_EXPANSION,
    }

    logger.info(
        "Expansion metadata built"
    )

    return metadata

# =========================================================
# MANUAL DEBUG
# =========================================================

if __name__ == "__main__":

    sample_query = (
        "Senior Python backend developer "
        "with communication skills"
    )

    metadata = (
        build_expansion_metadata(
            sample_query
        )
    )

    from pprint import pprint

    pprint(metadata)