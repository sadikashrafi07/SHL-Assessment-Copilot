# =========================================================
# app/services/reranker.py
# ENTERPRISE HYBRID RERANKER v15 ULTRA FINAL
# FULLY FIXED + SHL OPTIMIZED + ASSIGNMENT READY
# NO ARCHITECTURE CHANGE
# HIGH PRECISION + HIGH RECALL
# STRONG TECH MATCHING + SMART FILTERING
# ZERO IRRELEVANT RESULTS
# =========================================================

from __future__ import annotations

import logging
import math
import re

from collections import Counter
from functools import lru_cache
from typing import Any

from app.config.settings import (
    BM25_WEIGHT,
    COGNITIVE_MATCH_BOOST,
    COMMUNICATION_MATCH_BOOST,
    DOMAIN_MATCH_BOOST,
    ENABLE_DYNAMIC_EXPLANATIONS,
    ENABLE_FUZZY_MATCHING,
    ENABLE_RESULT_DIVERSITY,
    ENABLE_ROLE_PENALIZATION,
    ENABLE_SKILL_OVERLAP_SCORING,
    EXACT_PHRASE_BOOST,
    FINAL_RECOMMENDATIONS,
    HIGH_CONFIDENCE_THRESHOLD,
    IRRELEVANT_LEADERSHIP_PENALTY,
    KEYWORD_WEIGHT,
    LEXICAL_WEIGHT,
    LEADERSHIP_MATCH_BOOST,
    MAX_SAME_TYPE_RESULTS,
    MIN_ACCEPTABLE_SCORE,
    PHRASE_WEIGHT,
    ROLE_MATCH_BOOST,
    SEMANTIC_WEIGHT,
    SKILL_STRICT_MATCH_BOOST,
    TECH_STACK_MATCH_BOOST,
)

from app.utils.helpers import normalize

logger = logging.getLogger(__name__)

# =========================================================
# TOKENIZATION
# =========================================================

TOKEN_SPLIT_REGEX = re.compile(
    r"[\s,/|;:.()\[\]{}_\-+]+",
    re.IGNORECASE,
)

# =========================================================
# DOMAIN VOCABULARY
# =========================================================

DOMAIN_KEYWORDS = {

    "frontend": {
        "frontend",
        "react",
        "javascript",
        "typescript",
        "angular",
        "vue",
        "nextjs",
        "html",
        "css",
        "ui",
        "web",
    },

    "backend": {
        "backend",
        "python",
        "java",
        "spring",
        "django",
        "flask",
        "fastapi",
        "api",
        "microservices",
        "database",
        "sql",
        "distributed",
        "cloud",
        "aws",
        "docker",
        "kubernetes",
    },

    "devops": {
        "devops",
        "cloud",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "linux",
        "terraform",
        "jenkins",
        "ci/cd",
        "infrastructure",
        "monitoring",
        "automation",
    },

    "data_science": {
        "machine learning",
        "deep learning",
        "data science",
        "analytics",
        "statistics",
        "ai",
        "nlp",
        "llm",
        "predictive",
        "classification",
        "python",
        "visualization",
    },

    "leadership": {
        "leadership",
        "management",
        "stakeholder",
        "ownership",
        "strategy",
        "executive",
        "people management",
        "decision making",
        "organizational",
        "product manager",
    },

    "communication": {
        "communication",
        "presentation",
        "interpersonal",
        "collaboration",
        "verbal",
        "written",
        "cross functional",
        "client facing",
    },

    "cognitive": {
        "aptitude",
        "logical",
        "reasoning",
        "analytical",
        "problem solving",
        "critical thinking",
        "deductive",
    },
}

# =========================================================
# QUERY EXPANSIONS
# =========================================================

QUERY_EXPANSIONS = {

    "frontend": [
        "react",
        "javascript",
        "typescript",
        "html",
        "css",
        "ui",
        "web",
    ],

    "backend": [
        "python",
        "java",
        "api",
        "microservices",
        "distributed",
        "sql",
        "cloud",
        "aws",
        "docker",
        "kubernetes",
        "fastapi",
        "spring",
    ],

    "devops": [
        "docker",
        "kubernetes",
        "aws",
        "terraform",
        "cloud",
        "linux",
        "infrastructure",
        "ci/cd",
        "automation",
        "monitoring",
    ],

    "data scientist": [
        "machine learning",
        "deep learning",
        "analytics",
        "statistics",
        "python",
        "ai",
        "nlp",
        "llm",
    ],

    "product manager": [
        "stakeholder",
        "strategy",
        "management",
        "leadership",
        "communication",
        "collaboration",
    ],

    "leadership": [
        "stakeholder",
        "strategy",
        "management",
        "decision making",
    ],

    "communication": [
        "presentation",
        "collaboration",
        "interpersonal",
        "cross functional",
    ],

    "aptitude": [
        "reasoning",
        "logical",
        "analytical",
        "problem solving",
    ],
}

# =========================================================
# NEGATIVE TERMS
# =========================================================

NEGATIVE_TERMS = {

    "sample report",
    "feedback report",
    "administrator guide",
    "user guide",
    "practice report",
    "practice test",
    "demo report",
}

# =========================================================
# LOW QUALITY TERMS
# =========================================================

LOW_SIGNAL_TERMS = {

    "report",
    "feedback",
    "documentation",
    "guide",
}

# =========================================================
# HIGH VALUE TERMS
# =========================================================

HIGH_SIGNAL_TERMS = {

    "python",
    "java",
    "react",
    "docker",
    "kubernetes",
    "cloud",
    "machine learning",
    "analytics",
    "leadership",
    "communication",
    "aptitude",
    "reasoning",
    "problem solving",
    "aws",
    "fastapi",
    "microservices",
}

# =========================================================
# TECH TERMS
# =========================================================

TECHNICAL_TERMS = {

    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "angular",
    "vue",
    "docker",
    "kubernetes",
    "aws",
    "cloud",
    "sql",
    "api",
    "microservices",
    "backend",
    "frontend",
    "devops",
    "machine learning",
    "deep learning",
    "ai",
    "nlp",
    "terraform",
    "linux",
    "fastapi",
    "spring",
    "django",
    "flask",
}

# =========================================================
# TECH QUALITY TERMS
# =========================================================

TECHNICAL_QUALITY_TERMS = {

    "coding",
    "programming",
    "developer",
    "development",
    "technical",
    "simulation",
    "hands-on",
    "automation",
    "architecture",
    "engineering",
    "implementation",
    "debugging",
}

# =========================================================
# ROLE ALIASES
# =========================================================

ROLE_ALIASES = {
    "sde": "software engineer",
    "software developer": "software engineer",
    "frontend developer": "frontend",
    "backend developer": "backend",
    "ml engineer": "machine learning",
    "devops engineer": "devops",
}

# =========================================================
# NORMALIZATION
# =========================================================

@lru_cache(maxsize=10000)
def cached_normalize(text: str) -> str:
    return normalize(text or "")

# =========================================================
# TOKENIZER
# =========================================================

@lru_cache(maxsize=10000)
def tokenize(text: str) -> frozenset[str]:

    if not text:
        return frozenset()

    normalized = cached_normalize(text)

    tokens = {
        token.strip()
        for token in TOKEN_SPLIT_REGEX.split(normalized)
        if token.strip() and len(token.strip()) > 1
    }

    return frozenset(tokens)

# =========================================================
# SAFE HELPERS
# =========================================================

def safe_get(item, key, default=None):

    if isinstance(item, dict):
        return item.get(key, default)

    return getattr(item, key, default)

def safe_float(value, default=0.0):

    try:
        return float(value)
    except Exception:
        return default

# =========================================================
# QUERY CLEANING
# =========================================================

def clean_query(query: str) -> str:

    normalized = cached_normalize(query)

    for alias, replacement in ROLE_ALIASES.items():
        normalized = normalized.replace(alias, replacement)

    return normalized

# =========================================================
# QUERY ENRICHMENT
# =========================================================

def enrich_query(query: str) -> str:

    normalized = clean_query(query)

    expansions = [normalized]

    for trigger, values in QUERY_EXPANSIONS.items():

        if trigger in normalized:
            expansions.extend(values)

    deduped = list(dict.fromkeys(expansions))

    return " ".join(deduped)

# =========================================================
# SEARCHABLE TEXT
# =========================================================

def build_searchable_text(item):

    parts = []

    scalar_fields = [
        "name",
        "description",
        "summary",
        "category",
        "explanation",
    ]

    list_fields = [
        "skills",
        "competencies",
        "domains",
        "roles",
        "job_levels",
        "technical_skills",
        "leadership_traits",
        "communication_skills",
        "cognitive_traits",
        "keywords",
        "tags",
    ]

    for field in scalar_fields:

        value = safe_get(item, field)

        if value:
            parts.append(str(value))

    for field in list_fields:

        values = safe_get(item, field, [])

        if isinstance(values, list):

            parts.extend(
                str(v)
                for v in values
                if v
            )

    return cached_normalize(" ".join(parts))

# =========================================================
# INTENT DETECTION
# =========================================================

def infer_intents(query):

    normalized = cached_normalize(query)

    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():

        hits = sum(
            keyword in normalized
            for keyword in keywords
        )

        scores[domain] = min(hits / 3, 1.0)

    return scores

# =========================================================
# LEXICAL SCORE
# =========================================================

def lexical_score(query_terms, searchable_text):

    if not query_terms:
        return 0.0

    searchable_tokens = tokenize(searchable_text)

    exact_matches = len(
        query_terms.intersection(searchable_tokens)
    )

    fuzzy_matches = 0.0

    if ENABLE_FUZZY_MATCHING:

        for term in query_terms:

            if term in searchable_tokens:
                continue

            for token in searchable_tokens:

                if (
                    term in token
                    or token in term
                ):
                    fuzzy_matches += 0.20
                    break

    score = (
        exact_matches + fuzzy_matches
    ) / max(len(query_terms), 1)

    return round(min(score, 1.0), 4)

# =========================================================
# PHRASE SCORE
# =========================================================

def phrase_score(query, searchable_text):

    query_norm = cached_normalize(query)

    if query_norm in searchable_text:
        return EXACT_PHRASE_BOOST

    score = 0.0

    phrases = re.split(
        r",| and ",
        query_norm,
    )

    for phrase in phrases:

        phrase = phrase.strip()

        if len(phrase) < 4:
            continue

        if phrase in searchable_text:
            score += 0.05

    return min(score, 0.20)

# =========================================================
# DOMAIN ALIGNMENT
# =========================================================

def domain_alignment_score(
    query_terms,
    searchable_text,
):

    best_domain = "general"
    best_score = 0.0

    for domain, keywords in DOMAIN_KEYWORDS.items():

        overlap = sum(
            (
                keyword in searchable_text
                and keyword in query_terms
            )
            for keyword in keywords
        )

        score = overlap / max(len(keywords), 1)

        if score > best_score:
            best_score = score
            best_domain = domain

    return (
        min(best_score * 2.5, 0.30),
        best_domain,
    )

# =========================================================
# SKILL OVERLAP SCORE
# =========================================================

def skill_overlap_score(
    query_terms,
    searchable_text,
):

    overlap = 0

    for term in HIGH_SIGNAL_TERMS:

        if (
            term in query_terms
            and term in searchable_text
        ):
            overlap += 1

    score = overlap / max(
        len(HIGH_SIGNAL_TERMS),
        1,
    )

    return min(score * 3.0, 0.25)

# =========================================================
# TECH STACK SCORE
# =========================================================

def technical_stack_score(
    query_terms,
    searchable_text,
):

    overlap = 0

    for term in TECHNICAL_TERMS:

        if (
            term in query_terms
            and term in searchable_text
        ):
            overlap += 1

    if overlap == 0:
        return 0.0

    score = overlap / max(
        len(query_terms),
        1,
    )

    return min(score * 0.50, 0.35)

# =========================================================
# QUALITY SCORE
# =========================================================

def technical_quality_score(searchable_text):

    hits = sum(
        term in searchable_text
        for term in TECHNICAL_QUALITY_TERMS
    )

    return min(hits * 0.025, 0.12)

# =========================================================
# TEST TYPE BOOST
# =========================================================

def test_type_boost(
    intents,
    item,
):

    test_type = str(
        safe_get(item, "test_type", "K")
    ).upper()

    searchable_text = build_searchable_text(item)

    boost = 0.0

    technical_intent = (

        intents["frontend"] > 0.25
        or intents["backend"] > 0.25
        or intents["devops"] > 0.25
        or intents["data_science"] > 0.25
    )

    if technical_intent:

        if test_type == "K":
            boost += 0.16

        if any(
            term in searchable_text
            for term in TECHNICAL_QUALITY_TERMS
        ):
            boost += 0.08

    if intents["leadership"] > 0.25:

        if test_type in {"L", "P"}:
            boost += LEADERSHIP_MATCH_BOOST

    if intents["communication"] > 0.25:

        if test_type in {"S", "P", "A"}:
            boost += COMMUNICATION_MATCH_BOOST

    if intents["cognitive"] > 0.25:

        if test_type == "A":
            boost += COGNITIVE_MATCH_BOOST

    return min(boost, 0.30)

# =========================================================
# PENALTY
# =========================================================

def penalty_score(searchable_text):

    penalty = 0.0

    for term in NEGATIVE_TERMS:

        if term in searchable_text:
            penalty += 0.18

    for term in LOW_SIGNAL_TERMS:

        if term in searchable_text:
            penalty += 0.02

    return min(penalty, 0.40)

# =========================================================
# ROLE PENALTY
# =========================================================

def role_penalty(
    query_terms,
    searchable_text,
):

    if not ENABLE_ROLE_PENALIZATION:
        return 0.0

    leadership_terms = {
        "leadership",
        "stakeholder",
        "management",
        "strategy",
    }

    query_has_technical = any(
        t in query_terms
        for t in TECHNICAL_TERMS
    )

    leadership_heavy = sum(
        t in searchable_text
        for t in leadership_terms
    ) >= 2

    technical_content = any(
        term in searchable_text
        for term in TECHNICAL_QUALITY_TERMS
    )

    if (
        query_has_technical
        and leadership_heavy
        and not technical_content
    ):
        return IRRELEVANT_LEADERSHIP_PENALTY

    return 0.0

# =========================================================
# HARD FILTER
# =========================================================

def should_filter_result(
    query_terms,
    searchable_text,
):

    technical_query = any(
        term in query_terms
        for term in TECHNICAL_TERMS
    )

    if not technical_query:
        return False

    irrelevant_patterns = [

        "leadership report",
        "development report",
        "personality report",
        "narrative report",
        "feedback report",
        "candidate report",
        "sample report",
        "administrator guide",
    ]

    if any(
        pattern in searchable_text
        for pattern in irrelevant_patterns
    ):

        technical_content = any(
            term in searchable_text
            for term in TECHNICAL_QUALITY_TERMS
        )

        if not technical_content:
            return True

    return False

# =========================================================
# CONFIDENCE
# =========================================================

def compute_confidence(score):

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

def generate_explanation(domain):

    explanations = {

        "frontend":
            "Relevant for frontend engineering and modern web development.",

        "backend":
            "Relevant for backend systems, APIs, databases, and scalable services.",

        "devops":
            "Relevant for cloud infrastructure, Kubernetes, Docker, and DevOps workflows.",

        "data_science":
            "Relevant for machine learning, analytics, AI, and data science.",

        "leadership":
            "Supports leadership, strategy, and stakeholder management evaluation.",

        "communication":
            "Useful for communication, collaboration, and interpersonal assessment.",

        "cognitive":
            "Relevant for analytical reasoning, aptitude, and problem-solving.",
    }

    return explanations.get(
        domain,
        "Strong alignment with the requested hiring requirements.",
    )

# =========================================================
# DEDUPLICATION
# =========================================================

def canonicalize_name(name):

    name = cached_normalize(name)

    noise = [
        "(new)",
        "1.0",
        "2.0",
        "adaptive",
        "assessment",
        "simulation",
        "automata",
    ]

    for n in noise:
        name = name.replace(n, "")

    return name.strip()

# =========================================================
# MAIN RERANKER
# =========================================================

def rerank_results(results, query):

    try:

        if not results:
            return []

        enriched_query = enrich_query(query)

        query_terms = set(
            tokenize(enriched_query)
        )

        intents = infer_intents(
            enriched_query
        )

        reranked = []
        seen = set()

        for item in results:

            searchable_text = (
                build_searchable_text(item)
            )

            if not searchable_text:
                continue

            # =================================================
            # HARD FILTER
            # =================================================

            if should_filter_result(
                query_terms,
                searchable_text,
            ):
                continue

            # =================================================
            # DEDUPLICATION
            # =================================================

            canonical_name = (
                canonicalize_name(
                    safe_get(item, "name", "")
                )
            )

            if canonical_name in seen:
                continue

            seen.add(canonical_name)

            # =================================================
            # BASE SCORES
            # =================================================

            semantic_score = safe_float(
                safe_get(item, "score", 0.0)
            )

            bm25_score = safe_float(
                safe_get(item, "bm25_score", 0.0)
            )

            lexical = lexical_score(
                query_terms,
                searchable_text,
            )

            phrase = phrase_score(
                query,
                searchable_text,
            )

            domain_score, domain = (
                domain_alignment_score(
                    query_terms,
                    searchable_text,
                )
            )

            skill_score = (
                skill_overlap_score(
                    query_terms,
                    searchable_text,
                )
                if ENABLE_SKILL_OVERLAP_SCORING
                else 0.0
            )

            tech_score = technical_stack_score(
                query_terms,
                searchable_text,
            )

            quality_score = technical_quality_score(
                searchable_text
            )

            type_boost = test_type_boost(
                intents,
                item,
            )

            penalty = penalty_score(
                searchable_text
            )

            role_penalty_score = role_penalty(
                query_terms,
                searchable_text,
            )

            # =================================================
            # FINAL SCORE
            # =================================================

            final_score = (

                semantic_score * SEMANTIC_WEIGHT

                +

                bm25_score * BM25_WEIGHT

                +

                lexical * LEXICAL_WEIGHT

                +

                phrase * PHRASE_WEIGHT

                +

                domain_score * DOMAIN_MATCH_BOOST

                +

                skill_score * SKILL_STRICT_MATCH_BOOST

                +

                tech_score

                +

                quality_score

                +

                type_boost

                -

                penalty

                -

                role_penalty_score
            )

            # =================================================
            # AGREEMENT BOOSTS
            # =================================================

            if (
                semantic_score >= 0.70
                and lexical >= 0.30
            ):
                final_score += ROLE_MATCH_BOOST

            if domain_score >= 0.10:
                final_score += DOMAIN_MATCH_BOOST

            if skill_score >= 0.08:
                final_score += TECH_STACK_MATCH_BOOST

            if tech_score >= 0.12:
                final_score += 0.10

            if phrase >= 0.06:
                final_score += EXACT_PHRASE_BOOST

            # =================================================
            # NORMALIZATION
            # =================================================

            final_score = max(
                min(final_score, 1.0),
                0.0,
            )

            if final_score < MIN_ACCEPTABLE_SCORE:
                continue

            # =================================================
            # CONFIDENCE
            # =================================================

            confidence = compute_confidence(
                final_score
            )

            enriched = dict(item)

            enriched["score"] = round(
                final_score,
                4,
            )

            enriched["confidence"] = confidence

            enriched[
                "recommendation_strength"
            ] = (
                "high"
                if confidence >= HIGH_CONFIDENCE_THRESHOLD
                else (
                    "medium"
                    if confidence >= 0.68
                    else "low"
                )
            )

            enriched["matched_domain"] = domain

            if ENABLE_DYNAMIC_EXPLANATIONS:

                explanation_parts = []

                explanation_parts.append(
                    generate_explanation(domain)
                )

                if tech_score >= 0.10:
                    explanation_parts.append(
                        "Strong technical stack alignment."
                    )

                if quality_score >= 0.04:
                    explanation_parts.append(
                        "Hands-on technical assessment."
                    )

                if type_boost >= 0.10:
                    explanation_parts.append(
                        "Knowledge-focused assessment."
                    )

                enriched["explanation"] = " ".join(
                    explanation_parts
                )

            reranked.append(enriched)

        # =====================================================
        # SORT
        # =====================================================

        reranked.sort(
            key=lambda x: (
                x["score"],
                x["confidence"],
            ),
            reverse=True,
        )

        # =====================================================
        # DIVERSITY CONTROL
        # =====================================================

        final_results = []

        type_counts = Counter()

        technical_heavy = (

            intents["frontend"] > 0.30
            or intents["backend"] > 0.30
            or intents["devops"] > 0.30
            or intents["data_science"] > 0.30
        )

        leadership_heavy = (
            intents["leadership"] > 0.30
        )

        dynamic_limit = MAX_SAME_TYPE_RESULTS

        if technical_heavy:
            dynamic_limit = 5

        elif leadership_heavy:
            dynamic_limit = 3

        for item in reranked:

            test_type = str(
                item.get(
                    "test_type",
                    "K",
                )
            ).upper()

            if ENABLE_RESULT_DIVERSITY:

                if (
                    type_counts[test_type]
                    >= dynamic_limit
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
            "Final reranked results=%s",
            [
                (
                    r.get("name"),
                    r.get("score"),
                    r.get("confidence"),
                )
                for r in final_results
            ],
        )

        return final_results

    except Exception as error:

        logger.exception(
            "Reranking failed: %s",
            error,
        )

        return []