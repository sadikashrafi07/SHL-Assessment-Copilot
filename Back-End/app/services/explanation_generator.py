# =========================================================
# app/services/explanation_generator.py
# ENTERPRISE EXPLANATION ENGINE v8 FINAL
# FULLY FIXED + HIGH PRECISION + NO ROLE BLEEDING
# PRODUCTION GRADE + ASSIGNMENT READY
# NO ARCHITECTURE CHANGES
# =========================================================

from __future__ import annotations

import re

from collections import Counter
from functools import lru_cache
from typing import Any
from typing import Dict
from typing import List

# =========================================================
# ROLE EXPLANATIONS
# =========================================================

ROLE_EXPLANATIONS = {

    "frontend": (
        "Strong alignment with frontend engineering "
        "requirements including React, JavaScript, "
        "TypeScript, UI architecture, responsive "
        "web applications, accessibility, component-driven "
        "development, and modern frontend workflows."
    ),

    "backend": (
        "Strong alignment with backend engineering "
        "requirements including Python, Java, APIs, "
        "SQL, microservices, distributed systems, "
        "cloud-native services, Docker, Kubernetes, "
        "and scalable server-side architecture."
    ),

    "devops": (
        "Strong alignment with DevOps engineering "
        "requirements including AWS, cloud infrastructure, "
        "CI/CD pipelines, Docker, Kubernetes, Terraform, "
        "automation, deployment orchestration, monitoring, "
        "containerization, and platform engineering."
    ),

    "data_science": (
        "Strong alignment with machine learning, "
        "AI, analytics, NLP, predictive modeling, "
        "statistics, deep learning, LLMs, and "
        "data science workflows."
    ),

    "leadership": (
        "Strong alignment with leadership evaluation, "
        "stakeholder management, organizational strategy, "
        "people management, decision-making, "
        "and executive-level capabilities."
    ),

    "communication": (
        "Strong alignment with communication, "
        "presentation, collaboration, stakeholder "
        "interaction, interpersonal effectiveness, "
        "and business communication skills."
    ),

    "cognitive": (
        "Strong alignment with analytical reasoning, "
        "logical thinking, deductive reasoning, "
        "numerical analysis, critical thinking, "
        "and cognitive problem-solving ability."
    ),

    "situational": (
        "Strong alignment with situational judgement, "
        "real-world decision-making, workplace behavior, "
        "scenario-based evaluation, and practical execution."
    ),

    "general": (
        "Strong alignment with the requested "
        "hiring and assessment requirements."
    ),
}

# =========================================================
# INTENT KEYWORDS
# =========================================================

INTENT_KEYWORDS = {

    "frontend": {
        "frontend",
        "front end",
        "react",
        "reactjs",
        "nextjs",
        "vue",
        "vuejs",
        "angular",
        "typescript",
        "javascript",
        "html",
        "css",
        "ui",
        "ux",
        "responsive",
        "web",
        "jsx",
        "redux",
        "tailwind",
        "accessibility",
    },

    "backend": {
        "backend",
        "back end",
        "python",
        "java",
        "spring",
        "django",
        "flask",
        "fastapi",
        "rest",
        "graphql",
        "api",
        "apis",
        "sql",
        "database",
        "microservices",
        "distributed systems",
        "server",
        "node",
        "express",
        "web services",
        "scalable",
    },

    "devops": {
        "devops",
        "aws",
        "azure",
        "gcp",
        "cloud",
        "docker",
        "kubernetes",
        "terraform",
        "jenkins",
        "ci/cd",
        "linux",
        "monitoring",
        "deployment",
        "infrastructure",
        "containerization",
        "helm",
        "ansible",
        "platform engineering",
        "sre",
    },

    "data_science": {
        "machine learning",
        "deep learning",
        "nlp",
        "ai",
        "analytics",
        "data science",
        "statistics",
        "predictive modeling",
        "regression",
        "classification",
        "feature engineering",
        "pandas",
        "numpy",
        "neural network",
        "llm",
        "artificial intelligence",
        "tensorflow",
        "pytorch",
    },

    "leadership": {
        "leadership",
        "executive",
        "stakeholder",
        "organizational",
        "people management",
        "manager",
        "director",
        "strategy",
        "decision making",
        "ownership",
        "management",
        "team leadership",
        "program management",
    },

    "communication": {
        "communication",
        "presentation",
        "collaboration",
        "interpersonal",
        "verbal",
        "written",
        "business communication",
        "negotiation",
        "facilitation",
        "cross functional",
        "listening",
    },

    "cognitive": {
        "reasoning",
        "logical",
        "analytical",
        "critical thinking",
        "problem solving",
        "deductive",
        "numerical",
        "aptitude",
        "cognitive",
        "inductive",
    },

    "situational": {
        "situational",
        "judgement",
        "judgment",
        "scenario",
        "simulation",
        "behavioral",
        "managerial scenarios",
        "workplace behavior",
    },
}

# =========================================================
# NEGATIVE TERMS
# =========================================================

NEGATIVE_TERMS = {

    "sample report",
    "feedback report",
    "practice report",
    "development report",
    "candidate report",
    "narrative report",
    "user guide",
    "administrator guide",
    "telecommunication",
    "electronics",
    "signal processing",
}

# =========================================================
# HIGH SIGNAL TERMS
# =========================================================

HIGH_SIGNAL_TERMS = {

    "python",
    "java",
    "react",
    "javascript",
    "typescript",
    "docker",
    "kubernetes",
    "terraform",
    "aws",
    "cloud",
    "microservices",
    "sql",
    "api",
    "apis",
    "machine",
    "learning",
    "analytics",
    "ai",
    "nlp",
    "llm",
    "frontend",
    "backend",
    "devops",
}

# =========================================================
# TOKENIZATION
# =========================================================

TOKEN_SPLIT_REGEX = re.compile(
    r"[\s,/|;:.()\[\]{}_\-+]+",
    re.IGNORECASE,
)

# =========================================================
# NORMALIZATION
# =========================================================

@lru_cache(maxsize=10000)
def normalize_text(
    text: str,
) -> str:

    text = str(text or "").lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()

# =========================================================
# TOKENIZE
# =========================================================

@lru_cache(maxsize=10000)
def tokenize(
    text: str,
) -> frozenset[str]:

    if not text:
        return frozenset()

    normalized = normalize_text(text)

    return frozenset(
        token.strip()
        for token in TOKEN_SPLIT_REGEX.split(normalized)
        if token.strip() and len(token.strip()) > 1
    )

# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)

    except Exception:
        return default

# =========================================================
# CLEAN REASON
# =========================================================

def clean_reason(
    reason: str,
) -> str:

    if not reason:
        return ""

    cleaned = normalize_text(reason)

    replacements = {

        "semantic":
            "semantic relevance",

        "technical":
            "technical capability alignment",

        "communication":
            "communication capability alignment",

        "leadership":
            "leadership capability alignment",

        "cognitive":
            "cognitive ability alignment",

        "adaptive":
            "adaptive testing capability",

        "remote":
            "remote hiring capability",

        "frontend":
            "frontend engineering alignment",

        "backend":
            "backend engineering alignment",

        "devops":
            "DevOps capability alignment",
    }

    for source, target in replacements.items():

        cleaned = cleaned.replace(
            source,
            target,
        )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    )

    return cleaned.strip().capitalize()

# =========================================================
# BUILD SEARCHABLE TEXT
# =========================================================

def build_searchable_text(
    item: Dict[str, Any],
) -> str:

    parts: list[str] = []

    scalar_fields = [
        "name",
        "description",
        "summary",
        "explanation",
        "recommendation_reason",
        "category",
    ]

    list_fields = [
        "skills",
        "competencies",
        "domains",
        "roles",
        "tags",
        "technical_skills",
        "leadership_traits",
        "communication_skills",
        "matched_domains",
        "matched_roles",
        "matched_competencies",
        "keywords",
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

    return normalize_text(
        " ".join(parts)
    )

# =========================================================
# QUALITY CHECK
# =========================================================

def is_low_quality_content(
    searchable: str,
) -> bool:

    if not searchable:
        return True

    negative_hits = sum(
        1
        for term in NEGATIVE_TERMS
        if term in searchable
    )

    return negative_hits >= 2

# =========================================================
# ROLE DETECTION
# =========================================================

def detect_role_type(
    item: Dict[str, Any],
) -> str:

    searchable = build_searchable_text(item)

    if not searchable:
        return "general"

    searchable_tokens = tokenize(searchable)

    role_scores: dict[str, float] = {}

    for role, keywords in INTENT_KEYWORDS.items():

        score = 0.0

        for keyword in keywords:

            keyword_tokens = tokenize(keyword)

            if not keyword_tokens:
                continue

            overlap = keyword_tokens.intersection(
                searchable_tokens
            )

            overlap_ratio = (
                len(overlap) /
                max(len(keyword_tokens), 1)
            )

            # FULL EXACT MATCH
            if overlap_ratio == 1.0:

                if len(keyword_tokens) > 1:
                    score += 3.0
                else:
                    score += 1.5

            # PARTIAL MATCH
            elif overlap_ratio >= 0.5:
                score += 0.4

        role_scores[role] = score

    best_role = max(
        role_scores,
        key=role_scores.get,
    )

    best_score = role_scores[best_role]

    if best_score < 2.0:
        return "general"

    sorted_scores = sorted(
        role_scores.values(),
        reverse=True,
    )

    # PREVENT ROLE BLEEDING
    if (
        len(sorted_scores) > 1
        and (
            sorted_scores[0] -
            sorted_scores[1]
        ) < 1.2
    ):
        return "general"

    return best_role

# =========================================================
# MATCHED SKILLS
# =========================================================

def extract_matched_skills(
    query: str,
    item: Dict[str, Any],
) -> List[str]:

    searchable = build_searchable_text(item)

    normalized_query = normalize_text(query)

    if not normalized_query:
        return []

    searchable_tokens = tokenize(searchable)

    query_tokens = tokenize(
        normalized_query
    )

    overlap = query_tokens.intersection(
        searchable_tokens
    )

    prioritized: list[str] = []
    secondary: list[str] = []

    for token in overlap:

        if token in HIGH_SIGNAL_TERMS:
            prioritized.append(token)

        elif len(token) >= 4:
            secondary.append(token)

    prioritized = sorted(
        set(prioritized)
    )

    secondary = sorted(
        set(secondary)
    )

    unique = list(
        dict.fromkeys(
            prioritized + secondary
        )
    )

    return unique[:8]

# =========================================================
# CONFIDENCE LABEL
# =========================================================

def confidence_label(
    confidence: float,
) -> str:

    if confidence >= 0.92:
        return "exceptional"

    if confidence >= 0.84:
        return "very strong"

    if confidence >= 0.74:
        return "strong"

    if confidence >= 0.64:
        return "good"

    return "moderate"

# =========================================================
# TEST TYPE LABEL
# =========================================================

def readable_test_type(
    test_type: str,
) -> str:

    mapping = {

        "K": "knowledge-based",

        "A": "aptitude and cognitive",

        "P": "personality and behavioral",

        "S": "simulation-based",

        "L": "leadership-focused",
    }

    return mapping.get(
        str(test_type).upper(),
        "professional",
    )

# =========================================================
# DOMAIN SUMMARY
# =========================================================

def generate_domain_summary(
    item: Dict[str, Any],
) -> str:

    role = detect_role_type(item)

    return ROLE_EXPLANATIONS.get(
        role,
        ROLE_EXPLANATIONS["general"],
    )

# =========================================================
# TECH ALIGNMENT
# =========================================================

def generate_tech_alignment(
    matched_skills: List[str],
) -> str:

    if not matched_skills:
        return ""

    if len(matched_skills) == 1:

        return (
            f" Key aligned skill includes "
            f"{matched_skills[0]}."
        )

    return (
        " Key aligned skills include "
        + ", ".join(matched_skills[:5])
        + "."
    )

# =========================================================
# TECHNICAL BONUS
# =========================================================

def generate_technical_bonus(
    searchable: str,
) -> str:

    technical_terms = {
        "simulation",
        "hands-on",
        "coding",
        "developer",
        "automation",
        "practical",
        "compiler",
        "debugging",
    }

    if any(
        term in searchable
        for term in technical_terms
    ):

        return (
            " This assessment includes "
            "practical technical evaluation "
            "capabilities."
        )

    return ""

# =========================================================
# RECOMMENDATION REASON
# =========================================================

def generate_recommendation_reason(
    item: Dict[str, Any],
    query: str = "",
) -> str:

    searchable = build_searchable_text(item)

    role = detect_role_type(item)

    base_explanation = ROLE_EXPLANATIONS.get(
        role,
        ROLE_EXPLANATIONS["general"],
    )

    confidence = safe_float(
        item.get("confidence", 0.0)
    )

    score = round(
        safe_float(
            item.get("score", 0.0)
        ) * 100,
        1,
    )

    strength = confidence_label(
        confidence
    )

    test_type = readable_test_type(
        item.get("test_type", "")
    )

    matched_skills = extract_matched_skills(
        query,
        item,
    )

    skill_section = generate_tech_alignment(
        matched_skills
    )

    technical_bonus = generate_technical_bonus(
        searchable
    )

    adaptive_section = ""

    if item.get("adaptive") is True:

        adaptive_section = (
            " The assessment supports "
            "adaptive evaluation for "
            "improved measurement precision."
        )

    remote_section = ""

    if item.get("remote") is True:

        remote_section = (
            " It is suitable for scalable "
            "remote hiring workflows."
        )

    quality_note = ""

    if is_low_quality_content(searchable):

        quality_note = (
            " Some supporting metadata "
            "appears limited, but the "
            "assessment remains relevant."
        )

    return (
        f"{base_explanation} "
        f"This {test_type} assessment demonstrates "
        f"{strength} recommendation confidence "
        f"with an overall relevance score of "
        f"{score}%. "
        f"The recommendation is based on "
        f"semantic relevance, role alignment, "
        f"competency matching, skill overlap scoring, "
        f"and context-aware reranking."
        f"{skill_section}"
        f"{technical_bonus}"
        f"{adaptive_section}"
        f"{remote_section}"
        f"{quality_note}"
    )

# =========================================================
# SUMMARY
# =========================================================

def generate_summary(
    results: List[Dict[str, Any]],
) -> str:

    if not results:

        return (
            "No highly relevant assessments "
            "were identified for the provided "
            "hiring requirements."
        )

    top = results[0]

    top_name = top.get(
        "name",
        "the selected assessment",
    )

    confidence = round(
        safe_float(
            top.get("confidence", 0.0)
        ) * 100
    )

    score = round(
        safe_float(
            top.get("score", 0.0)
        ) * 100
    )

    test_type = readable_test_type(
        top.get("test_type", "")
    )

    domains: list[str] = []

    for item in results[:5]:

        role = detect_role_type(item)

        if role != "general":
            domains.append(role)

    domain_summary = ""

    if domains:

        common_domains = [
            domain
            for domain, _
            in Counter(domains).most_common(3)
        ]

        domain_summary = (
            " The recommendations primarily focus on "
            + ", ".join(common_domains)
            + " evaluation areas."
        )

    return (
        f"The strongest recommendation is "
        f"{top_name}, a {test_type} assessment "
        f"with {confidence}% confidence and "
        f"{score}% relevance alignment."
        f"{domain_summary}"
    )

# =========================================================
# MULTI RESULT ENHANCEMENT
# =========================================================

def generate_combined_explanation(
    results: List[Dict[str, Any]],
    query: str = "",
) -> List[Dict[str, Any]]:

    enhanced_results: list[Dict[str, Any]] = []

    for rank, item in enumerate(
        results,
        start=1,
    ):

        enhanced = dict(item)

        enhanced["rank"] = rank

        enhanced["role_type"] = (
            detect_role_type(enhanced)
        )

        enhanced["domain_summary"] = (
            generate_domain_summary(
                enhanced
            )
        )

        enhanced[
            "recommendation_reason"
        ] = generate_recommendation_reason(
            enhanced,
            query,
        )

        enhanced_results.append(
            enhanced
        )

    return enhanced_results

# =========================================================
# TOP PICK REASON
# =========================================================

def generate_top_pick_reason(
    item: Dict[str, Any],
) -> str:

    role = detect_role_type(item)

    role_text = ROLE_EXPLANATIONS.get(
        role,
        ROLE_EXPLANATIONS["general"],
    )

    confidence = safe_float(
        item.get("confidence", 0.0)
    )

    strength = confidence_label(
        confidence
    )

    score = round(
        safe_float(
            item.get("score", 0.0)
        ) * 100,
        1,
    )

    return (
        f"This assessment is the strongest "
        f"overall recommendation because it "
        f"demonstrates {strength} alignment "
        f"with the target hiring requirements "
        f"and achieved a relevance score of "
        f"{score}%. "
        f"{role_text}"
    )

# =========================================================
# PUBLIC EXPORTS
# =========================================================

__all__ = [

    "generate_recommendation_reason",

    "generate_summary",

    "generate_combined_explanation",

    "generate_top_pick_reason",

    "generate_domain_summary",

    "detect_role_type",

    "extract_matched_skills",

    "confidence_label",

    "readable_test_type",

    "clean_reason",
]