# =========================================================
# app/services/query_parser.py
# ENTERPRISE QUERY PARSER v6
# FULLY FIXED + ASSIGNMENT OPTIMIZED
# SAME ARCHITECTURE PRESERVED
# =========================================================

from __future__ import annotations

import re

from difflib import get_close_matches
from functools import lru_cache
from typing import Dict
from typing import List
from typing import Set

from app.config.settings import (
    ENABLE_COMPETENCY_EXPANSION,
    ENABLE_FUZZY_MATCHING,
    ENABLE_QUERY_EXPANSION,
    ENABLE_ROLE_EXPANSION,
    MAX_EXPANSION_TERMS,
    QUERY_EXPANSIONS,
    ROLE_COMPETENCIES,
)

from app.utils.helpers import normalize

# =========================================================
# FUZZY CONFIG
# =========================================================

FUZZY_MATCH_THRESHOLD = 0.86

MAX_FUZZY_RESULTS = 2

MIN_TOKEN_LENGTH = 3

# =========================================================
# ROLE ALIASES
# =========================================================

ROLE_ALIASES = {

    "sde": "software engineer",
    "software developer": "software engineer",

    "backend engineer": "backend developer",
    "frontend engineer": "frontend developer",

    "fullstack developer": "full stack developer",
    "fullstack engineer": "full stack developer",

    "ml engineer": "data scientist",
    "machine learning engineer": "data scientist",
    "ai engineer": "data scientist",

    "pm": "product manager",
    "product owner": "product manager",

    "engineering lead": "engineering manager",
    "tech lead": "engineering manager",
}

# =========================================================
# VOCABULARY
# =========================================================

TECHNICAL_TERMS: Dict[str, int] = {

    "developer": 2,
    "software": 1,
    "engineer": 2,
    "technical": 2,
    "coding": 3,
    "programming": 3,
    "software development": 4,
    "system design": 5,
    "debugging": 3,
    "algorithms": 5,

    "python": 5,
    "java": 5,
    "javascript": 5,
    "typescript": 5,
    "sql": 5,

    "frontend": 5,
    "react": 5,
    "angular": 4,
    "vue": 4,
    "ui": 3,
    "ux": 3,
    "nextjs": 5,
    "redux": 4,
    "tailwind": 4,

    "backend": 5,
    "api": 5,
    "microservices": 5,
    "distributed systems": 5,
    "fastapi": 5,
    "django": 4,
    "flask": 4,
    "node": 4,

    "cloud": 4,
    "aws": 5,
    "docker": 5,
    "kubernetes": 5,
    "linux": 4,
    "devops": 5,
    "infrastructure": 4,

    "machine learning": 5,
    "deep learning": 4,
    "artificial intelligence": 5,
    "ai": 5,
    "analytics": 4,
    "statistics": 5,
    "data science": 5,
    "data analysis": 5,
    "nlp": 5,
    "tensorflow": 5,
    "pytorch": 5,

    "problem solving": 5,
    "analytical thinking": 5,
}

COMMUNICATION_TERMS: Dict[str, int] = {

    "communication": 5,
    "stakeholder management": 5,
    "stakeholder communication": 5,
    "presentation": 4,
    "collaboration": 4,
    "cross functional": 4,
    "interpersonal": 4,
    "client facing": 5,
    "written communication": 5,
    "verbal communication": 5,
    "negotiation": 4,
    "facilitation": 3,
}

LEADERSHIP_TERMS: Dict[str, int] = {

    "leadership": 5,
    "management": 4,
    "manager": 4,
    "people management": 5,
    "decision making": 5,
    "strategic thinking": 5,
    "ownership": 3,
    "team lead": 4,
    "executive": 4,
    "organizational leadership": 5,
}

PERSONALITY_TERMS: Dict[str, int] = {

    "personality": 5,
    "behavioral": 5,
    "behavior": 4,
    "motivation": 4,
    "adaptability": 4,
    "resilience": 4,
    "culture fit": 4,
    "traits": 3,
    "opq": 5,
}

COGNITIVE_TERMS: Dict[str, int] = {

    "cognitive": 5,
    "aptitude": 5,
    "reasoning": 5,
    "logical reasoning": 5,
    "analytical": 5,
    "critical thinking": 5,
    "numerical": 4,
    "problem solving": 5,
    "deductive": 4,
    "inductive": 4,
    "general ability": 5,
}

# =========================================================
# ROLE TERMS
# =========================================================

ROLE_TERMS = {

    "software engineer",
    "backend developer",
    "frontend developer",
    "full stack developer",
    "java developer",
    "python developer",
    "data scientist",
    "product manager",
    "engineering manager",
    "devops engineer",
    "analyst",
    "consultant",
    "designer",
    "sales professional",
}

# =========================================================
# SENIORITY
# =========================================================

SENIORITY_TERMS = {

    "entry",
    "entry level",
    "junior",
    "associate",
    "mid",
    "senior",
    "lead",
    "principal",
    "manager",
    "executive",
}

# =========================================================
# DELIVERY
# =========================================================

DELIVERY_TERMS = {

    "remote",
    "adaptive",
    "online",
    "virtual",
    "mobile",
}

# =========================================================
# NEGATION
# =========================================================

NEGATION_TERMS = {

    "not",
    "without",
    "exclude",
    "excluding",
    "avoid",
    "except",
    "no",
}

# =========================================================
# COMPARISON
# =========================================================

COMPARISON_TERMS = {

    "compare",
    "comparison",
    "difference",
    "vs",
    "versus",
    "better than",
    "alternative",
    "which is better",
}

# =========================================================
# CATEGORY MAP
# =========================================================

CATEGORY_MAP = {

    "technical": TECHNICAL_TERMS,
    "communication": COMMUNICATION_TERMS,
    "leadership": LEADERSHIP_TERMS,
    "personality": PERSONALITY_TERMS,
    "cognitive": COGNITIVE_TERMS,
}

# =========================================================
# ALL TERMS
# =========================================================

ALL_TERMS = {

    *TECHNICAL_TERMS.keys(),
    *COMMUNICATION_TERMS.keys(),
    *LEADERSHIP_TERMS.keys(),
    *PERSONALITY_TERMS.keys(),
    *COGNITIVE_TERMS.keys(),
    *ROLE_TERMS,
    *SENIORITY_TERMS,
    *DELIVERY_TERMS,
}

MULTI_WORD_TERMS = sorted(
    ALL_TERMS,
    key=len,
    reverse=True,
)

# =========================================================
# NORMALIZATION
# =========================================================

@lru_cache(maxsize=10000)
def normalize_cached(
    text: str,
) -> str:

    text = normalize(text or "")

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()

# =========================================================
# REGEX CACHE
# =========================================================

@lru_cache(maxsize=10000)
def build_word_pattern(
    term: str,
) -> re.Pattern:

    return re.compile(
        rf"\b{re.escape(normalize_cached(term))}\b",
        flags=re.IGNORECASE,
    )

# =========================================================
# SAFE REGEX
# =========================================================

def regex_match(
    term: str,
    text: str,
) -> bool:

    if not term or not text:
        return False

    return bool(
        build_word_pattern(term).search(text)
    )

# =========================================================
# NORMALIZE ROLE
# =========================================================

def normalize_role(
    role: str,
) -> str:

    role = normalize_cached(role)

    return ROLE_ALIASES.get(
        role,
        role,
    )

# =========================================================
# TOKENIZER
# =========================================================

def tokenize_query(
    query: str,
) -> List[str]:

    query = normalize_cached(query)

    protected_query = query

    phrases = []

    for phrase in MULTI_WORD_TERMS:

        if regex_match(
            phrase,
            query,
        ):

            phrases.append(phrase)

            protected_query = re.sub(
                build_word_pattern(phrase),
                phrase.replace(" ", "_"),
                protected_query,
            )

    raw_tokens = re.findall(
        r"\b[\w\-/+#.]+\b",
        protected_query,
    )

    normalized_tokens = []

    for token in raw_tokens:

        cleaned = normalize_cached(
            token.replace("_", " ")
        )

        if len(cleaned) >= MIN_TOKEN_LENGTH:
            normalized_tokens.append(cleaned)

    normalized_tokens.extend(phrases)

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

    normalized_query = normalize_cached(query)

    patterns = [

        rf"\b(?:not|without|exclude|excluding|avoid|except|no)\s+{re.escape(term)}\b",

        rf"\b{re.escape(term)}\s+(?:is\s+)?not\s+required\b",

        rf"\bwithout\s+(?:any\s+)?{re.escape(term)}\b",
    ]

    return any(
        re.search(
            pattern,
            normalized_query,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )

# =========================================================
# EXTRACTION
# =========================================================

def extract_matches(
    query: str,
    vocabulary,
) -> List[str]:

    matches = []

    for term in vocabulary:

        if (
            regex_match(term, query)
            and not detect_negation(query, term)
        ):

            matches.append(term)

    return sorted(set(matches))

# =========================================================
# FUZZY MATCH
# =========================================================

def fuzzy_match(
    token: str,
    vocabulary,
) -> List[str]:

    if len(token) < MIN_TOKEN_LENGTH:
        return []

    return get_close_matches(
        token,
        vocabulary,
        n=MAX_FUZZY_RESULTS,
        cutoff=FUZZY_MATCH_THRESHOLD,
    )

# =========================================================
# FUZZY EXTRACTION
# =========================================================

def extract_fuzzy_matches(
    query: str,
    vocabulary,
) -> List[str]:

    if not ENABLE_FUZZY_MATCHING:
        return []

    detected: Set[str] = set()

    tokens = tokenize_query(query)

    for token in tokens:

        if token in vocabulary:
            continue

        matches = fuzzy_match(
            token,
            vocabulary,
        )

        for match in matches:

            if not detect_negation(query, match):
                detected.add(match)

    return sorted(detected)

# =========================================================
# INTENT WEIGHTS
# =========================================================

def calculate_intent_weights(
    query: str,
) -> Dict[str, int]:

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
                and not detect_negation(query, term)
            ):

                weights[category] += score

    return weights

# =========================================================
# PRIMARY INTENT
# =========================================================

def determine_primary_intent(
    weights: Dict[str, int],
) -> str:

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
# CONFIDENCE
# =========================================================

def calculate_confidence(
    weights: Dict[str, int],
) -> float:

    total = sum(weights.values())

    if total <= 0:
        return 0.0

    dominant = max(weights.values())

    confidence = (
        dominant / total
    )

    confidence = (
        confidence * 0.85
    ) + (
        min(total / 40, 1.0) * 0.15
    )

    return round(
        min(confidence, 1.0),
        3,
    )

# =========================================================
# ROLE EXPANSION
# =========================================================

def expand_roles(
    roles: List[str],
) -> List[str]:

    if not ENABLE_ROLE_EXPANSION:
        return []

    expanded = []

    for role in roles:

        normalized_role = normalize_role(role)

        expanded.extend(
            ROLE_COMPETENCIES.get(
                normalized_role,
                [],
            )
        )

    return sorted(set(expanded))

# =========================================================
# QUERY EXPANSION
# =========================================================

def expand_query(
    query: str,
    detected_skills: List[str],
    detected_roles: List[str],
    detected_assessment_types: List[str],
) -> str:

    if not ENABLE_QUERY_EXPANSION:
        return query

    expanded_terms = [query]

    for (
        keyword,
        values,
    ) in QUERY_EXPANSIONS.items():

        if regex_match(
            keyword,
            query,
        ):
            expanded_terms.extend(values)

    for skill in detected_skills:

        expanded_terms.extend(
            QUERY_EXPANSIONS.get(
                skill,
                [],
            )
        )

    if ENABLE_COMPETENCY_EXPANSION:

        expanded_terms.extend(
            expand_roles(
                detected_roles
            )
        )

    expanded_terms.extend(
        detected_assessment_types
    )

    unique_terms = []

    seen = set()

    for term in expanded_terms:

        normalized_term = normalize_cached(term)

        if (
            normalized_term
            and normalized_term not in seen
        ):

            seen.add(normalized_term)

            unique_terms.append(
                normalized_term
            )

    unique_terms = unique_terms[
        :MAX_EXPANSION_TERMS
    ]

    return " ".join(unique_terms)

# =========================================================
# COMPARISON
# =========================================================

def detect_comparison_query(
    query: str,
) -> bool:

    return any(
        regex_match(term, query)
        for term in COMPARISON_TERMS
    )

# =========================================================
# DELIVERY
# =========================================================

def extract_delivery_preferences(
    query: str,
) -> List[str]:

    return extract_matches(
        query,
        DELIVERY_TERMS,
    )

# =========================================================
# ASSESSMENT TYPES
# =========================================================

def extract_assessment_types(
    weights: Dict[str, int],
) -> List[str]:

    return sorted([

        category

        for (
            category,
            score,
        ) in weights.items()

        if score > 0
    ])

# =========================================================
# MAIN PARSER
# =========================================================

def parse_query(
    query: str,
) -> Dict:

    normalized_query = normalize_cached(query)

    tokens = tokenize_query(
        normalized_query
    )

    intent_weights = (
        calculate_intent_weights(
            normalized_query
        )
    )

    exact_skills = extract_matches(
        normalized_query,
        TECHNICAL_TERMS.keys(),
    )

    fuzzy_skills = extract_fuzzy_matches(
        normalized_query,
        TECHNICAL_TERMS.keys(),
    )

    all_skills = sorted(
        set(
            exact_skills
            + fuzzy_skills
        )
    )

    exact_roles = extract_matches(
        normalized_query,
        ROLE_TERMS,
    )

    fuzzy_roles = extract_fuzzy_matches(
        normalized_query,
        ROLE_TERMS,
    )

    detected_roles = sorted(
        set(
            normalize_role(role)

            for role in (
                exact_roles
                + fuzzy_roles
            )
        )
    )

    detected_seniority = extract_matches(
        normalized_query,
        SENIORITY_TERMS,
    )

    delivery_preferences = (
        extract_delivery_preferences(
            normalized_query
        )
    )

    assessment_types = (
        extract_assessment_types(
            intent_weights
        )
    )

    expanded_query = expand_query(
        normalized_query,
        all_skills,
        detected_roles,
        assessment_types,
    )

    return {

        "technical":
            intent_weights["technical"] > 0,

        "communication":
            intent_weights["communication"] > 0,

        "leadership":
            intent_weights["leadership"] > 0,

        "personality":
            intent_weights["personality"] > 0,

        "cognitive":
            intent_weights["cognitive"] > 0,

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

        "comparison":
            detect_comparison_query(
                normalized_query
            ),

        "roles":
            detected_roles,

        "seniority":
            detected_seniority,

        "skills":
            all_skills,

        "delivery_preferences":
            delivery_preferences,

        "assessment_types":
            assessment_types,

        "expanded_query":
            expanded_query,

        "normalized_query":
            normalized_query,

        "tokens":
            tokens,
    }

# =========================================================
# DEBUG
# =========================================================

if __name__ == "__main__":

    from pprint import pprint

    sample_query = (
        "Senior backend engineer with "
        "python, microservices, aws, "
        "stakeholder management and "
        "leadership experience"
    )

    pprint(
        parse_query(
            sample_query
        )
    )