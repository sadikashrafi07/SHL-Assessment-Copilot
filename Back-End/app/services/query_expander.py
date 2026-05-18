# =========================================================
# app/services/query_expander.py
# Enterprise-Grade Semantic Query Expansion Engine
# FULLY FIXED + HIGH RECALL + LOW MEMORY OPTIMIZED
# =========================================================

from __future__ import annotations

import logging
import re

from functools import lru_cache

from typing import Any
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple

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

MIN_WEIGHT_THRESHOLD = 0.60

MAX_WEIGHT = 1.0

MIN_TERM_LENGTH = 2

# =========================================================
# ROLE INTELLIGENCE
# =========================================================

ROLE_CONTEXT_MAP: Dict[str, List[str]] = {

    "software engineer": [
        "technical",
        "backend",
        "frontend",
    ],

    "software developer": [
        "technical",
        "backend",
        "frontend",
    ],

    "backend developer": [
        "backend",
        "api",
    ],

    "backend engineer": [
        "backend",
        "api",
    ],

    "frontend developer": [
        "frontend",
        "ui",
    ],

    "frontend engineer": [
        "frontend",
        "ui",
    ],

    "full stack developer": [
        "frontend",
        "backend",
    ],

    "full stack engineer": [
        "frontend",
        "backend",
    ],

    "data scientist": [
        "data",
        "analytics",
    ],

    "machine learning engineer": [
        "data",
        "analytics",
    ],

    "devops engineer": [
        "devops",
        "cloud",
    ],

    "product manager": [
        "leadership",
        "communication",
    ],

    "engineering manager": [
        "leadership",
        "communication",
    ],
}

# =========================================================
# QUERY EXPANSIONS
# =========================================================

QUERY_EXPANSIONS: Dict[
    str,
    Dict[str, List[Tuple[str, float]]],
] = {

    # =====================================================
    # PYTHON
    # =====================================================

    "python": {

        "general": [
            ("programming", 0.92),
            ("software engineer", 0.90),
            ("coding", 0.88),
            ("automation", 0.82),
            ("technical assessment", 0.78),
        ],

        "backend": [
            ("backend", 0.95),
            ("api", 0.90),
            ("microservices", 0.88),
            ("django", 0.92),
            ("flask", 0.90),
            ("fastapi", 0.95),
            ("server side", 0.82),
            ("sql", 0.84),
            ("distributed systems", 0.82),
        ],

        "data": [
            ("machine learning", 0.95),
            ("data science", 0.92),
            ("analytics", 0.88),
            ("ai", 0.90),
            ("statistics", 0.82),
            ("pandas", 0.88),
            ("numpy", 0.84),
        ],
    },

    # =====================================================
    # JAVA
    # =====================================================

    "java": {

        "general": [
            ("programming", 0.90),
            ("software engineer", 0.90),
            ("coding", 0.88),
        ],

        "backend": [
            ("spring", 0.95),
            ("spring boot", 0.95),
            ("microservices", 0.90),
            ("backend", 0.88),
            ("api", 0.82),
            ("distributed systems", 0.84),
        ],
    },

    # =====================================================
    # JAVASCRIPT
    # =====================================================

    "javascript": {

        "frontend": [
            ("react", 0.95),
            ("frontend", 0.92),
            ("web development", 0.88),
            ("ui", 0.82),
            ("typescript", 0.88),
            ("responsive design", 0.80),
        ],

        "backend": [
            ("node", 0.92),
            ("nodejs", 0.92),
            ("express", 0.88),
            ("api", 0.80),
        ],
    },

    # =====================================================
    # TYPESCRIPT
    # =====================================================

    "typescript": {

        "frontend": [
            ("react", 0.95),
            ("angular", 0.90),
            ("frontend", 0.92),
            ("ui", 0.82),
            ("javascript", 0.88),
        ],

        "backend": [
            ("nodejs", 0.90),
            ("backend", 0.85),
            ("api", 0.78),
        ],
    },

    # =====================================================
    # REACT
    # =====================================================

    "react": {

        "frontend": [
            ("javascript", 0.95),
            ("typescript", 0.90),
            ("frontend", 0.95),
            ("ui", 0.88),
            ("web development", 0.90),
            ("redux", 0.82),
        ]
    },

    # =====================================================
    # CLOUD
    # =====================================================

    "cloud": {

        "general": [
            ("aws", 0.95),
            ("azure", 0.92),
            ("gcp", 0.92),
            ("infrastructure", 0.82),
        ],

        "devops": [
            ("docker", 0.95),
            ("kubernetes", 0.95),
            ("devops", 0.92),
            ("deployment", 0.82),
            ("automation", 0.80),
        ],
    },

    # =====================================================
    # DEVOPS
    # =====================================================

    "devops": {

        "general": [
            ("docker", 0.95),
            ("kubernetes", 0.95),
            ("jenkins", 0.88),
            ("ci/cd", 0.88),
            ("deployment", 0.82),
            ("linux", 0.80),
            ("cloud", 0.88),
        ]
    },

    # =====================================================
    # COMMUNICATION
    # =====================================================

    "communication": {

        "general": [
            ("stakeholder management", 0.95),
            ("presentation", 0.92),
            ("collaboration", 0.90),
            ("client communication", 0.88),
            ("verbal communication", 0.82),
            ("cross functional collaboration", 0.88),
        ]
    },

    # =====================================================
    # LEADERSHIP
    # =====================================================

    "leadership": {

        "general": [
            ("management", 0.95),
            ("decision making", 0.90),
            ("ownership", 0.85),
            ("strategic thinking", 0.88),
            ("team leadership", 0.88),
            ("people management", 0.92),
        ]
    },

    # =====================================================
    # COGNITIVE
    # =====================================================

    "cognitive": {

        "general": [
            ("reasoning", 0.95),
            ("aptitude", 0.92),
            ("logical reasoning", 0.90),
            ("problem solving", 0.92),
            ("analytical thinking", 0.88),
            ("critical thinking", 0.90),
        ]
    },

    # =====================================================
    # PERSONALITY
    # =====================================================

    "personality": {

        "general": [
            ("behavioral", 0.95),
            ("behavior", 0.88),
            ("culture fit", 0.85),
            ("motivation", 0.82),
            ("adaptability", 0.82),
            ("traits", 0.78),
            ("opq", 0.95),
        ]
    },

    # =====================================================
    # PRODUCT MANAGER
    # =====================================================

    "product manager": {

        "general": [
            ("stakeholder management", 0.95),
            ("roadmapping", 0.92),
            ("strategy", 0.90),
            ("leadership", 0.88),
            ("communication", 0.88),
            ("cross functional collaboration", 0.85),
        ]
    },

    # =====================================================
    # SOFTWARE ENGINEER
    # =====================================================

    "software engineer": {

        "general": [
            ("coding", 0.95),
            ("algorithms", 0.92),
            ("problem solving", 0.92),
            ("technical assessment", 0.90),
            ("debugging", 0.82),
            ("software development", 0.90),
        ]
    },

    # =====================================================
    # DATA SCIENTIST
    # =====================================================

    "data scientist": {

        "general": [
            ("machine learning", 0.95),
            ("statistics", 0.92),
            ("analytics", 0.92),
            ("python", 0.90),
            ("data analysis", 0.90),
            ("ai", 0.88),
        ]
    },
}

# =========================================================
# CONTEXT TERMS
# =========================================================

CONTEXT_TERMS: Dict[
    str,
    Set[str],
] = {

    "backend": {
        "backend",
        "api",
        "microservices",
        "server",
        "django",
        "flask",
        "fastapi",
        "spring",
        "sql",
        "database",
    },

    "frontend": {
        "frontend",
        "ui",
        "react",
        "angular",
        "web",
        "javascript",
        "typescript",
        "css",
        "html",
    },

    "data": {
        "data",
        "analytics",
        "machine learning",
        "ai",
        "statistics",
        "deep learning",
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

    "leadership": {
        "leadership",
        "management",
        "stakeholder",
        "strategy",
    },

    "communication": {
        "communication",
        "presentation",
        "collaboration",
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
    "which is better",
}

# =========================================================
# PHRASES
# =========================================================

MULTI_WORD_PHRASES: List[str] = sorted(
    {
        "software engineer",
        "software developer",
        "backend developer",
        "frontend developer",
        "full stack developer",
        "data scientist",
        "product manager",
        "machine learning",
        "problem solving",
        "critical thinking",
        "stakeholder management",
        "people management",
        "cross functional collaboration",
        "technical assessment",
        "logical reasoning",
        "analytical thinking",
        "behavioral traits",
        "distributed systems",
        "software development",
        "web development",
    },
    key=len,
    reverse=True,
)

# =========================================================
# REGEX HELPERS
# =========================================================

@lru_cache(maxsize=4096)
def build_word_pattern(
    term: str,
) -> re.Pattern:

    return re.compile(
        rf"\b{re.escape(normalize(term))}\b",
        flags=re.IGNORECASE,
    )


def regex_match(
    term: str,
    text: str,
) -> bool:

    if not term or not text:
        return False

    return bool(
        build_word_pattern(term).search(
            normalize(text)
        )
    )

# =========================================================
# TOKENIZER
# =========================================================

def tokenize_query(
    query: str,
) -> List[str]:

    if not query:
        return []

    normalized_query = normalize(query)

    detected_phrases: List[str] = []

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

    raw_tokens = re.findall(
        r"\b[\w\-/+#.]+\b",
        normalized_query,
    )

    tokens: List[str] = []

    for token in raw_tokens:

        cleaned = normalize(
            token.replace("_", " ")
        )

        if (
            cleaned
            and len(cleaned) >= MIN_TERM_LENGTH
        ):
            tokens.append(cleaned)

    tokens.extend(detected_phrases)

    return list(
        dict.fromkeys(tokens)
    )

# =========================================================
# CONTEXT DETECTION
# =========================================================

def detect_query_context(
    tokens: List[str],
) -> List[str]:

    contexts: Set[str] = set()

    for token in tokens:

        for (
            context,
            keywords,
        ) in CONTEXT_TERMS.items():

            if token in keywords:
                contexts.add(context)

    for token in tokens:

        role_contexts = ROLE_CONTEXT_MAP.get(
            token,
            [],
        )

        contexts.update(role_contexts)

    if not contexts:
        contexts.add(GENERAL_CONTEXT)

    return sorted(contexts)

# =========================================================
# COMPARISON DETECTION
# =========================================================

def is_comparison_query(
    query: str,
) -> bool:

    normalized_query = normalize(query)

    return any(
        regex_match(term, normalized_query)
        for term in COMPARISON_TERMS
    )

# =========================================================
# TERM COMPRESSION
# =========================================================

def compress_terms(
    weighted_terms: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

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

        if existing is None:

            compressed[term] = item
            continue

        existing_weight = float(
            existing.get("weight", 0.0)
        )

        current_weight = float(
            item.get("weight", 0.0)
        )

        if current_weight > existing_weight:
            compressed[term] = item

    return sorted(
        compressed.values(),
        key=lambda x: (
            float(x.get("weight", 0.0)),
            x.get("term", ""),
        ),
        reverse=True,
    )

# =========================================================
# WEIGHT VALIDATION
# =========================================================

def sanitize_weight(
    value: float,
) -> float:

    try:
        value = float(value)

    except (
        TypeError,
        ValueError,
    ):
        value = DEFAULT_WEIGHT

    value = max(
        0.0,
        min(value, MAX_WEIGHT),
    )

    return round(value, 3)

# =========================================================
# EXPANSION ENGINE
# =========================================================

def _build_weighted_terms(
    query: str,
) -> List[Dict[str, Any]]:

    if not query:
        return []

    normalized_query = normalize(query)

    if not normalized_query:
        return []

    if not ENABLE_QUERY_EXPANSION:

        return [
            {
                "term": normalized_query,
                "weight": 1.0,
                "source": "disabled",
                "context": "disabled",
            }
        ]

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
                "source": "comparison",
                "context": "comparison",
            }
        ]

    # =====================================================
    # TOKENIZATION
    # =====================================================

    tokens = tokenize_query(
        normalized_query
    )

    if not tokens:
        return []

    contexts = detect_query_context(
        tokens
    )

    weighted_terms: List[
        Dict[str, Any]
    ] = []

    seen: Set[str] = set()

    # =====================================================
    # ORIGINAL QUERY
    # =====================================================

    weighted_terms.append(
        {
            "term": normalized_query,
            "weight": 1.0,
            "source": "query",
            "context": "primary",
        }
    )

    seen.add(normalized_query)

    # =====================================================
    # ORIGINAL TOKENS
    # =====================================================

    for token in tokens:

        if token in seen:
            continue

        weighted_terms.append(
            {
                "term": token,
                "weight": 0.98,
                "source": "original",
                "context": "primary",
            }
        )

        seen.add(token)

    # =====================================================
    # SEMANTIC EXPANSION
    # =====================================================

    for token in tokens:

        expansion_map = QUERY_EXPANSIONS.get(
            token
        )

        if not expansion_map:
            continue

        applicable_contexts = list(
            dict.fromkeys(
                contexts + [GENERAL_CONTEXT]
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

                validated_weight = sanitize_weight(
                    weight
                )

                if (
                    context == GENERAL_CONTEXT
                ):
                    validated_weight *= 0.92

                validated_weight = round(
                    validated_weight,
                    3,
                )

                if (
                    validated_weight
                    < MIN_WEIGHT_THRESHOLD
                ):
                    continue

                weighted_terms.append(
                    {
                        "term":
                            normalized_term,

                        "weight":
                            validated_weight,

                        "source":
                            token,

                        "context":
                            context,
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

    weighted_terms = (
        _build_weighted_terms(query)
    )

    logger.info(
        "Expansion terms=%s",
        len(weighted_terms),
    )

    return weighted_terms


def build_expansion_metadata(
    query: str,
) -> Dict[str, Any]:

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

    return {

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

# =========================================================
# DEBUG
# =========================================================

if __name__ == "__main__":

    sample_query = (
        "Senior Python backend developer "
        "with leadership and communication skills"
    )

    from pprint import pprint

    pprint(
        build_expansion_metadata(
            sample_query
        )
    )