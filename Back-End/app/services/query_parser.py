# =========================================================
# app/services/query_parser.py
# =========================================================
"""
Enterprise-grade query parser for:
- intent detection
- semantic skill extraction
- fuzzy matching
- role detection
- comparison detection
- delivery preference extraction
- structured retrieval metadata

Improvements:
✔ Removed duplicated logic
✔ Removed unnecessary regex passes
✔ Added caching
✔ Added type hints
✔ Added deterministic outputs
✔ Added safer fuzzy matching
✔ Added weighted scoring normalization
✔ Added phrase-aware extraction
✔ Added negative intent handling
✔ Added extensibility
✔ Improved retrieval precision
✔ Improved reranker compatibility
✔ Reduced noisy classifications
✔ Production-ready architecture
"""

from __future__ import annotations

import re
from difflib import get_close_matches
from functools import lru_cache
from typing import Dict, List, Set, Tuple

from app.utils.helpers import normalize

# =========================================================
# CONFIG
# =========================================================

FUZZY_MATCH_THRESHOLD = 0.85
MAX_FUZZY_RESULTS = 1

# =========================================================
# DOMAIN VOCABULARY
# =========================================================

TECHNICAL_TERMS: Dict[str, int] = {
    "developer": 2,
    "software": 1,
    "programming": 2,
    "coding": 2,
    "engineer": 2,
    "technical": 1,
    "python": 5,
    "java": 5,
    "javascript": 5,
    "react": 4,
    "node": 4,
    "backend": 4,
    "frontend": 4,
    "full stack": 5,
    "cloud": 4,
    "aws": 5,
    "sql": 4,
    "docker": 4,
    "linux": 3,
    "api": 3,
    "machine learning": 5,
    "ai": 5,
    "devops": 4,
}

COMMUNICATION_TERMS: Dict[str, int] = {
    "communication": 5,
    "stakeholder": 4,
    "presentation": 4,
    "email": 2,
    "verbal": 3,
    "writing": 3,
    "collaboration": 4,
    "interpersonal": 4,
    "client facing": 5,
}

PERSONALITY_TERMS: Dict[str, int] = {
    "personality": 5,
    "behavioral": 5,
    "behavior": 4,
    "culture": 3,
    "traits": 3,
    "motivation": 4,
    "adaptability": 4,
    "opq": 5,
}

LEADERSHIP_TERMS: Dict[str, int] = {
    "leadership": 5,
    "manager": 4,
    "management": 4,
    "decision making": 4,
    "team lead": 4,
    "ownership": 3,
    "strategic": 3,
}

COGNITIVE_TERMS: Dict[str, int] = {
    "cognitive": 5,
    "aptitude": 5,
    "reasoning": 4,
    "logical": 3,
    "critical thinking": 4,
    "analytical": 4,
    "numerical": 4,
    "problem solving": 5,
}

# =========================================================
# ENTITY TERMS
# =========================================================

ROLE_TERMS = {
    "developer",
    "engineer",
    "manager",
    "analyst",
    "consultant",
    "architect",
    "sales",
    "support",
    "designer",
    "intern",
    "graduate",
}

SENIORITY_TERMS = {
    "entry",
    "junior",
    "mid",
    "senior",
    "lead",
    "principal",
    "manager",
}

COMPARISON_TERMS = {
    "compare",
    "comparison",
    "difference",
    "vs",
    "versus",
    "better than",
    "alternative to",
    "which is better",
}

NEGATION_TERMS = {
    "not",
    "don't",
    "do not",
    "without",
    "exclude",
    "avoid",
    "no",
}

DELIVERY_TERMS = {
    "remote",
    "adaptive",
    "online",
    "virtual",
}

# =========================================================
# SYNONYM MAP
# =========================================================

SYNONYMS = {
    "developer": [
        "engineer",
        "programmer",
        "software developer",
        "software engineer",
    ],

    "communication": [
        "stakeholder",
        "presentation",
        "collaboration",
        "client communication",
    ],

    "leadership": [
        "management",
        "ownership",
        "team leadership",
    ],

    "cloud": [
        "aws",
        "azure",
        "gcp",
    ],

    "backend": [
        "api",
        "microservices",
        "server side",
    ],

    "personality": [
        "behavioral",
        "culture fit",
        "traits",
    ],
}

# =========================================================
# CATEGORY MAPPING
# =========================================================

CATEGORY_MAP = {
    "technical": TECHNICAL_TERMS,
    "communication": COMMUNICATION_TERMS,
    "personality": PERSONALITY_TERMS,
    "leadership": LEADERSHIP_TERMS,
    "cognitive": COGNITIVE_TERMS,
}

# =========================================================
# PHRASE TERMS
# =========================================================

MULTI_WORD_TERMS = sorted(
    {
        *TECHNICAL_TERMS.keys(),
        *COMMUNICATION_TERMS.keys(),
        *PERSONALITY_TERMS.keys(),
        *LEADERSHIP_TERMS.keys(),
        *COGNITIVE_TERMS.keys(),
    },
    key=len,
    reverse=True,
)

# =========================================================
# REGEX HELPERS
# =========================================================

@lru_cache(maxsize=2048)
def build_word_pattern(term: str) -> re.Pattern:
    """
    Cached whole-word regex pattern.
    """

    return re.compile(
        rf"\b{re.escape(normalize(term))}\b",
        flags=re.IGNORECASE,
    )


def regex_match(term: str, text: str) -> bool:
    """
    Safe whole-word match.
    """

    if not term or not text:
        return False

    return bool(
        build_word_pattern(term).search(text)
    )

# =========================================================
# TOKENIZATION
# =========================================================

def tokenize_query(query: str) -> List[str]:
    """
    Phrase-aware tokenizer.
    """

    normalized_query = normalize(query)

    protected_query = normalized_query

    detected_phrases = []

    for phrase in MULTI_WORD_TERMS:

        if regex_match(phrase, normalized_query):

            detected_phrases.append(phrase)

            protected_query = re.sub(
                build_word_pattern(phrase),
                phrase.replace(" ", "_"),
                protected_query,
            )

    tokens = re.findall(
        r"\b[\w\-/]+\b",
        protected_query,
    )

    normalized_tokens = [
        normalize(
            token.replace("_", " ")
        )
        for token in tokens
    ]

    normalized_tokens.extend(
        detected_phrases
    )

    # deterministic unique ordering
    return list(
        dict.fromkeys(normalized_tokens)
    )

# =========================================================
# NEGATION DETECTION
# =========================================================

def detect_negation(
    query: str,
    term: str,
) -> bool:
    """
    Detect negated intent.
    Example:
    - "not python"
    - "without leadership"
    """

    for negation in NEGATION_TERMS:

        pattern = (
            rf"\b{re.escape(negation)}\s+"
            rf"{re.escape(term)}\b"
        )

        if re.search(
            pattern,
            query,
            flags=re.IGNORECASE,
        ):
            return True

    return False

# =========================================================
# GENERIC EXTRACTION
# =========================================================

def extract_matches(
    query: str,
    vocabulary,
) -> List[str]:
    """
    Extract exact matches from vocabulary.
    """

    matches = []

    for term in vocabulary:

        if (
            regex_match(term, query)
            and not detect_negation(
                query,
                term,
            )
        ):
            matches.append(term)

    return sorted(set(matches))

# =========================================================
# FUZZY MATCHING
# =========================================================

def fuzzy_match(
    token: str,
    vocabulary,
) -> str | None:
    """
    Fuzzy skill correction.
    """

    matches = get_close_matches(
        token,
        vocabulary,
        n=MAX_FUZZY_RESULTS,
        cutoff=FUZZY_MATCH_THRESHOLD,
    )

    return matches[0] if matches else None


def extract_fuzzy_matches(
    query: str,
    vocabulary,
) -> List[str]:
    """
    Extract fuzzy matched skills.
    """

    detected: Set[str] = set()

    tokens = tokenize_query(query)

    for token in tokens:

        fuzzy = fuzzy_match(
            token,
            vocabulary,
        )

        if fuzzy:
            detected.add(fuzzy)

    return sorted(detected)

# =========================================================
# INTENT DETECTION
# =========================================================

def detect_query_type(
    query: str,
    vocabulary,
) -> bool:
    """
    Detect category presence.
    """

    return bool(
        extract_matches(
            query,
            vocabulary,
        )
    )

# =========================================================
# INTENT WEIGHTS
# =========================================================

def calculate_intent_weights(
    query: str,
) -> Dict[str, int]:
    """
    Weighted category scoring.
    """

    weights = {
        category: 0
        for category in CATEGORY_MAP
    }

    for (
        category,
        vocabulary,
    ) in CATEGORY_MAP.items():

        for (
            term,
            score,
        ) in vocabulary.items():

            if (
                regex_match(term, query)
                and not detect_negation(
                    query,
                    term,
                )
            ):
                weights[category] += score

    return weights

# =========================================================
# CONFIDENCE
# =========================================================

def calculate_confidence(
    weights: Dict[str, int],
) -> float:
    """
    Confidence based on dominant intent.
    """

    total = sum(weights.values())

    if total <= 0:
        return 0.0

    dominant = max(weights.values())

    return round(
        dominant / total,
        3,
    )

# =========================================================
# PRIMARY INTENT
# =========================================================

def determine_primary_intent(
    weights: Dict[str, int],
) -> str:
    """
    Determine dominant intent.
    """

    if not weights:
        return "general"

    dominant = max(
        weights.values(),
        default=0,
    )

    if dominant <= 0:
        return "general"

    return max(
        weights,
        key=weights.get,
    )

# =========================================================
# QUERY EXPANSION
# =========================================================

def expand_query(query: str) -> str:
    """
    Lightweight synonym expansion.
    """

    normalized_query = normalize(query)

    expanded_terms = [
        normalized_query
    ]

    for (
        keyword,
        synonyms,
    ) in SYNONYMS.items():

        if regex_match(
            keyword,
            normalized_query,
        ):
            expanded_terms.extend(
                synonyms
            )

    unique_terms = list(
        dict.fromkeys(
            normalize(term)
            for term in expanded_terms
        )
    )

    return " ".join(unique_terms)

# =========================================================
# ENTITY EXTRACTION
# =========================================================

def extract_delivery_preferences(
    query: str,
) -> List[str]:
    return extract_matches(
        query,
        DELIVERY_TERMS,
    )


def extract_assessment_types(
    weights: Dict[str, int],
) -> List[str]:
    """
    Extract active assessment types.
    """

    return sorted(
        [
            category
            for (
                category,
                score,
            ) in weights.items()
            if score > 0
        ]
    )

# =========================================================
# COMPARISON DETECTION
# =========================================================

def detect_comparison_query(
    query: str,
) -> bool:
    """
    Detect comparison-style queries.
    """

    return any(
        regex_match(term, query)
        for term in COMPARISON_TERMS
    )

# =========================================================
# MAIN PARSER
# =========================================================

def parse_query(
    query: str,
) -> Dict:
    """
    Enterprise-grade structured query parser.
    """

    normalized_query = normalize(query)

    # =====================================================
    # INTENT WEIGHTS
    # =====================================================

    intent_weights = (
        calculate_intent_weights(
            normalized_query
        )
    )

    # =====================================================
    # FUZZY TECHNICAL SKILLS
    # =====================================================

    fuzzy_skills = (
        extract_fuzzy_matches(
            normalized_query,
            TECHNICAL_TERMS.keys(),
        )
    )

    exact_skills = extract_matches(
        normalized_query,
        TECHNICAL_TERMS.keys(),
    )

    all_skills = sorted(
        set(
            exact_skills + fuzzy_skills
        )
    )

    # =====================================================
    # OUTPUT
    # =====================================================

    parsed = {

        # -----------------------------
        # category detection
        # -----------------------------
        "technical":
            intent_weights["technical"] > 0,

        "communication":
            intent_weights["communication"] > 0,

        "personality":
            intent_weights["personality"] > 0,

        "leadership":
            intent_weights["leadership"] > 0,

        "cognitive":
            intent_weights["cognitive"] > 0,

        # -----------------------------
        # query type
        # -----------------------------
        "comparison":
            detect_comparison_query(
                normalized_query
            ),

        # -----------------------------
        # intent analysis
        # -----------------------------
        "primary_intent":
            determine_primary_intent(
                intent_weights
            ),

        "intent_confidence":
            calculate_confidence(
                intent_weights
            ),

        "intent_weights":
            intent_weights,

        # -----------------------------
        # extracted entities
        # -----------------------------
        "roles":
            extract_matches(
                normalized_query,
                ROLE_TERMS,
            ),

        "seniority":
            extract_matches(
                normalized_query,
                SENIORITY_TERMS,
            ),

        "skills":
            all_skills,

        "delivery_preferences":
            extract_delivery_preferences(
                normalized_query
            ),

        "assessment_types":
            extract_assessment_types(
                intent_weights
            ),

        # -----------------------------
        # query expansion
        # -----------------------------
        "expanded_query":
            expand_query(
                normalized_query
            ),

        # -----------------------------
        # metadata
        # -----------------------------
        "normalized_query":
            normalized_query,

        "tokens":
            tokenize_query(
                normalized_query
            ),
    }

    return parsed

# =========================================================
# DEBUG
# =========================================================

if __name__ == "__main__":

    sample_query = (
        "Senior Python backend developer "
        "with stakeholder communication "
        "and leadership skills"
    )

    from pprint import pprint

    pprint(
        parse_query(sample_query)
    )