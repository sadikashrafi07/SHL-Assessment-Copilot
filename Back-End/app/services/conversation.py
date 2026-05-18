# =========================================================
# app/services/conversation.py
# Production-Grade Conversation Understanding Engine
# FULLY FIXED ENTERPRISE VERSION
# =========================================================

from __future__ import annotations

import logging
import re
from typing import Any

from app.utils.helpers import normalize

logger = logging.getLogger(__name__)

# =========================================================
# CONSTANTS
# =========================================================

COMPARISON_WORDS = {
    "compare",
    "comparison",
    "difference",
    "versus",
    "vs",
    "better than",
    "alternative",
}

REFINEMENT_WORDS = {
    "actually",
    "instead",
    "update",
    "modify",
    "change",
    "replace",
    "refine",
}

END_WORDS = {
    "thanks",
    "thank you",
    "bye",
    "done",
    "goodbye",
    "perfect",
    "great",
}

# =========================================================
# GREETING WORDS
# =========================================================

GREETING_WORDS = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "yo",
    "hola",
}

# =========================================================
# HELP WORDS
# =========================================================

HELP_WORDS = {
    "help",
    "what can you do",
    "how can you help",
    "features",
    "capabilities",
}

# =========================================================
# STRONG OFFTOPIC FILTERS
# =========================================================

OFFTOPIC_WORDS = {

    # Finance
    "salary",
    "crypto",
    "bitcoin",
    "investment",
    "stock",
    "trading",

    # Politics
    "politics",
    "government",
    "election",

    # Cyber
    "hack",
    "malware",
    "exploit",
    "torrent",

    # Food
    "biryani",
    "biriyani",
    "pizza",
    "burger",
    "food",

    # Casual
    "movie",
    "music",
    "song",
    "cricket",
    "football",
    "relationship",
    "girlfriend",
    "boyfriend",

    # Random
    "weather",
    "tourism",
    "travel",
    "hotel",
    "news",
}

# =========================================================
# DOMAIN KEYWORDS
# =========================================================

DOMAIN_KEYWORDS = {

    # =====================================================
    # Hiring
    # =====================================================

    "assessment",
    "assessment test",
    "assessment recommendation",
    "assessment recommendations",

    "test",
    "testing",

    "hiring",
    "recruitment",
    "recruiting",

    "candidate",
    "candidate screening",
    "screening",

    "interview",
    "evaluation",
    "hiring evaluation",

    "job",
    "role",
    "position",

    # =====================================================
    # Assessment Types
    # =====================================================

    "technical assessment",
    "coding assessment",
    "personality assessment",
    "leadership assessment",
    "cognitive assessment",
    "aptitude test",

    # =====================================================
    # Roles
    # =====================================================

    "developer",
    "engineer",
    "manager",
    "architect",
    "analyst",
    "designer",

    # =====================================================
    # Skills
    # =====================================================

    "python",
    "java",
    "sql",
    "aws",
    "react",
    "docker",
    "leadership",
    "communication",
    "aptitude",
    "cognitive",
}

# =========================================================
# ROLE TAXONOMY
# =========================================================

ROLE_PATTERNS = sorted(
    [
        # Product
        "senior product manager",
        "associate product manager",
        "product manager",
        "product owner",
        "program manager",
        "project manager",

        # Engineering
        "software engineer",
        "software developer",
        "backend engineer",
        "backend developer",
        "frontend engineer",
        "frontend developer",
        "full stack developer",
        "full stack engineer",
        "qa engineer",
        "test engineer",
        "devops engineer",
        "cloud engineer",
        "site reliability engineer",
        "sre",
        "data engineer",
        "machine learning engineer",
        "ai engineer",

        # Analytics
        "data scientist",
        "data analyst",
        "business analyst",

        # Management
        "engineering manager",
        "marketing manager",
        "sales manager",
        "hr manager",
        "scrum master",

        # Design
        "ux designer",
        "ui designer",
        "product designer",

        # Generic
        "developer",
        "engineer",
        "manager",
        "analyst",
        "designer",
        "architect",
        "intern",
        "graduate",
    ],
    key=len,
    reverse=True,
)

# =========================================================
# SENIORITY
# =========================================================

SENIORITY_PATTERNS = [
    "principal",
    "staff",
    "lead",
    "senior",
    "mid",
    "junior",
    "entry",
    "associate",
]

# =========================================================
# ASSESSMENT TYPES
# =========================================================

ASSESSMENT_TYPES = [
    "technical",
    "personality",
    "behavioral",
    "behavioural",
    "cognitive",
    "communication",
    "leadership",
    "coding",
    "aptitude",
    "situational",
]

# =========================================================
# SKILLS
# =========================================================

SKILL_PATTERNS = sorted(
    [
        # Languages
        "python",
        "java",
        "javascript",
        "typescript",
        "sql",
        "scala",
        "go",
        "golang",
        "rust",

        # Frontend
        "react",
        "angular",
        "vue",
        "html",
        "css",

        # Backend
        "spring boot",
        "spring",
        "nodejs",
        "node",
        "microservices",
        "api",
        "fastapi",
        "django",
        "flask",

        # Cloud
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "terraform",

        # Data
        "tableau",
        "power bi",
        "analytics",
        "machine learning",
        "deep learning",
        "data science",
        "statistics",

        # Product
        "roadmap",
        "product strategy",
        "stakeholder management",
        "stakeholder communication",
        "stakeholder",
        "strategy",
        "execution",
        "prioritization",

        # Leadership
        "leadership",
        "communication",
        "presentation",
        "people management",

        # AI
        "artificial intelligence",
        "generative ai",
        "llm",
        "ai",

        # Domains
        "backend",
        "frontend",
        "full stack",
        "devops",
        "cloud",
    ],
    key=len,
    reverse=True,
)

# =========================================================
# REGEX HELPERS
# =========================================================

def build_pattern(term: str) -> re.Pattern:
    """
    Safe whole-word regex pattern.
    """

    return re.compile(
        rf"\b{re.escape(normalize(term))}\b",
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
        build_pattern(term).search(text)
    )

# =========================================================
# NORMALIZATION
# =========================================================

def normalize_text(text: Any) -> str:
    """
    Normalize arbitrary text safely.
    """

    if text is None:
        return ""

    text = str(text)

    text = normalize(text)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()

# =========================================================
# EXTRACTION HELPERS
# =========================================================

def deduplicate(
    items: list[str],
) -> list[str]:
    """
    Deterministic deduplication.
    """

    cleaned: list[str] = []

    for item in items:

        value = normalize_text(item)

        if value and value not in cleaned:
            cleaned.append(value)

    return cleaned


def extract_roles(
    text: str,
) -> list[str]:
    """
    Extract role mentions.
    """

    text = normalize_text(text)

    found: list[str] = []

    for role in ROLE_PATTERNS:

        if regex_match(role, text):
            found.append(role)

    return deduplicate(found)


def extract_seniority(
    text: str,
) -> str | None:
    """
    Extract seniority level.
    """

    text = normalize_text(text)

    for level in SENIORITY_PATTERNS:

        if regex_match(level, text):
            return level

    return None


def extract_assessment_types(
    text: str,
) -> list[str]:
    """
    Extract assessment types.
    """

    text = normalize_text(text)

    found: list[str] = []

    for assessment_type in ASSESSMENT_TYPES:

        if regex_match(
            assessment_type,
            text,
        ):
            found.append(assessment_type)

    return deduplicate(found)


def extract_skills(
    text: str,
) -> list[str]:
    """
    Extract technical + professional skills.
    """

    text = normalize_text(text)

    found: list[str] = []

    for skill in SKILL_PATTERNS:

        if regex_match(skill, text):
            found.append(skill)

    return deduplicate(found)

# =========================================================
# DOMAIN VALIDATION
# =========================================================

def is_relevant_query(
    text: str,
) -> bool:
    """
    Validate whether query belongs to
    SHL assessment recommendation domain.
    """

    text = normalize_text(text)

    if not text:
        return False

    # =====================================================
    # GREETINGS + HELP ARE ALLOWED
    # =====================================================

    if any(
        regex_match(word, text)
        for word in GREETING_WORDS
    ):
        return True

    if any(
        regex_match(word, text)
        for word in HELP_WORDS
    ):
        return True

    # =====================================================
    # HARDCODED OFFTOPIC FILTER
    # =====================================================

    if any(
        regex_match(word, text)
        for word in OFFTOPIC_WORDS
    ):
        return False

    # =====================================================
    # DOMAIN SIGNALS
    # =====================================================

    role_matches = extract_roles(text)

    skill_matches = extract_skills(text)

    assessment_matches = (
        extract_assessment_types(text)
    )

    keyword_matches = any(
        regex_match(word, text)
        for word in DOMAIN_KEYWORDS
    )

    return bool(
        role_matches
        or skill_matches
        or assessment_matches
        or keyword_matches
    )

# =========================================================
# MESSAGE HELPERS
# =========================================================

def get_latest_user_message(
    messages: list[Any],
) -> str:
    """
    Get latest user message safely.
    """

    for msg in reversed(messages):

        role = (
            msg.get("role")
            if isinstance(msg, dict)
            else getattr(msg, "role", "")
        )

        content = (
            msg.get("content")
            if isinstance(msg, dict)
            else getattr(msg, "content", "")
        )

        role_value = (
            role.value
            if hasattr(role, "value")
            else str(role)
        )

        if role_value == "user":
            return str(content or "")

    return ""


def build_conversation_text(
    messages: list[Any],
) -> str:
    """
    Build normalized conversation text.
    """

    parts: list[str] = []

    for msg in messages:

        content = (
            msg.get("content")
            if isinstance(msg, dict)
            else getattr(msg, "content", "")
        )

        if content:
            parts.append(str(content))

    return normalize_text(
        " ".join(parts)
    )

# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intent(
    messages: list[Any],
) -> str:
    """
    Detect conversational intent safely.
    """

    latest = normalize_text(
        get_latest_user_message(messages)
    )

    if not latest:
        return "recommendation"

    # =====================================================
    # GREETING
    # =====================================================

    if any(
        regex_match(word, latest)
        for word in GREETING_WORDS
    ):
        return "greeting"

    # =====================================================
    # HELP
    # =====================================================

    if any(
        regex_match(word, latest)
        for word in HELP_WORDS
    ):
        return "help"

    # =====================================================
    # DOMAIN VALIDATION
    # =====================================================

    if not is_relevant_query(latest):
        return "offtopic"

    # =====================================================
    # COMPARISON
    # =====================================================

    if (
        " vs " in latest
        or any(
            regex_match(word, latest)
            for word in COMPARISON_WORDS
        )
    ):
        return "comparison"

    # =====================================================
    # REFINEMENT
    # =====================================================

    if any(
        latest.startswith(word)
        for word in REFINEMENT_WORDS
    ):
        return "refinement"

    return "recommendation"

# =========================================================
# EXTRACTION HELPERS
# =========================================================

def extract_duration_constraint(
    text: str,
) -> int | None:
    """
    Extract duration limits.
    """

    text = normalize_text(text)

    patterns = [
        r"under (\d+)\s*(mins|minutes)",
        r"less than (\d+)\s*(mins|minutes)",
        r"within (\d+)\s*(mins|minutes)",
        r"(\d+)\s*(mins|minutes) max",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:
            return int(match.group(1))

    return None


def extract_experience(
    text: str,
) -> str | None:
    """
    Extract years of experience.
    """

    text = normalize_text(text)

    match = re.search(
        r"(\d+)\+?\s*(years|yrs|year)",
        text,
    )

    if match:
        return match.group(1)

    return None


def extract_comparison_targets(
    text: str,
) -> list[str]:
    """
    Extract comparison targets.
    """

    text = normalize_text(text)

    if " vs " in text:

        return deduplicate(
            [
                x.strip()
                for x in text.split(" vs ")
                if x.strip()
            ]
        )[:2]

    match = re.search(
        r"compare (.+?) and (.+)",
        text,
    )

    if match:

        return deduplicate(
            [
                match.group(1).strip(),
                match.group(2).strip(),
            ]
        )[:2]

    return []

# =========================================================
# CONTEXT EXTRACTION
# =========================================================

def extract_context(
    messages: list[Any],
) -> dict[str, Any]:
    """
    Extract structured conversation context.
    """

    text = build_conversation_text(
        messages
    )

    latest_message = normalize_text(
        get_latest_user_message(messages)
    )

    intent = detect_intent(messages)

    roles = extract_roles(text)

    if (
        not roles
        and regex_match(
            "data scientist",
            text,
        )
    ):
        roles.append("data scientist")

    skills = extract_skills(text)

    leadership_required = any(
        regex_match(term, text)
        for term in [
            "leadership",
            "manager",
            "management",
            "team lead",
        ]
    )

    communication_required = any(
        regex_match(term, text)
        for term in [
            "communication",
            "stakeholder",
            "presentation",
            "collaboration",
        ]
    )

    personality_required = any(
        regex_match(term, text)
        for term in [
            "personality",
            "behavioral",
            "behavioural",
            "culture fit",
        ]
    )

    cognitive_required = any(
        regex_match(term, text)
        for term in [
            "cognitive",
            "reasoning",
            "analytical",
            "problem solving",
            "aptitude",
        ]
    )

    context = {

        "roles":
            deduplicate(roles),

        "seniority":
            extract_seniority(text),

        "skills":
            skills,

        "assessment_types":
            extract_assessment_types(text),

        "duration_limit":
            extract_duration_constraint(text),

        "experience":
            extract_experience(text),

        "remote_required":
            regex_match(
                "remote",
                text,
            ),

        "adaptive_required":
            regex_match(
                "adaptive",
                text,
            ),

        "leadership_required":
            leadership_required,

        "communication_required":
            communication_required,

        "personality_required":
            personality_required,

        "cognitive_required":
            cognitive_required,

        "comparison_targets":
            [],

        "raw_query":
            latest_message,

        "intent":
            intent,
    }

    if intent == "comparison":

        context[
            "comparison_targets"
        ] = extract_comparison_targets(
            latest_message
        )

    logger.info(
        "Extracted context: %s",
        context,
    )

    return context

# =========================================================
# CLARIFICATION
# =========================================================

def should_ask_clarification(
    context: dict[str, Any],
    messages: list[Any],
) -> dict[str, Any]:
    """
    Determine whether clarification is needed.
    """

    if context.get("intent") in {
        "offtopic",
        "greeting",
        "help",
    }:

        return {
            "needed": False,
            "missing_fields": [],
            "offtopic": False,
        }

    has_signal = any(
        [
            context.get("roles"),
            context.get("skills"),
            context.get("assessment_types"),
            context.get("leadership_required"),
            context.get("communication_required"),
            context.get("cognitive_required"),
            context.get("personality_required"),
        ]
    )

    if has_signal:

        return {
            "needed": False,
            "missing_fields": [],
            "offtopic": False,
        }

    if len(messages) >= 4:

        return {
            "needed": False,
            "missing_fields": [],
            "offtopic": False,
        }

    return {
        "needed": True,
        "missing_fields": [
            "role",
            "skills",
        ],
        "offtopic": False,
    }


def generate_clarification_question(
    missing_fields: list[str],
    offtopic: bool = False,
) -> str:
    """
    Generate clarification question safely.
    """

    if offtopic:

        return (
            "Please ask queries related to "
            "SHL assessments, hiring roles, "
            "skills, or competency evaluation."
        )

    return (
        "Could you share the target role, "
        "seniority level, and key technical "
        "or professional skills you want "
        "to evaluate?"
    )

# =========================================================
# SEARCH QUERY
# =========================================================

def build_search_query(
    context: dict[str, Any],
) -> str:
    """
    Build optimized retrieval query.
    """

    if context.get("intent") in {
        "offtopic",
        "greeting",
        "help",
    }:
        return ""

    parts: list[str] = []

    parts.extend(
        context.get("roles", [])
    )

    if context.get("seniority"):

        parts.append(
            context["seniority"]
        )

    parts.extend(
        context.get("skills", [])
    )

    parts.extend(
        context.get(
            "assessment_types",
            [],
        )
    )

    if context.get(
        "leadership_required"
    ):
        parts.append("leadership")

    if context.get(
        "communication_required"
    ):
        parts.append("communication")

    if context.get(
        "personality_required"
    ):
        parts.append("personality")

    if context.get(
        "cognitive_required"
    ):
        parts.append("cognitive")

    if context.get(
        "adaptive_required"
    ):
        parts.append("adaptive")

    if context.get(
        "remote_required"
    ):
        parts.append("remote")

    if context.get("experience"):

        parts.append(
            f"{context['experience']} years"
        )

    query = " ".join(
        deduplicate(parts)
    )

    query = normalize_text(query)

    logger.info(
        "Final search query: %s",
        query,
    )

    return query

# =========================================================
# END DETECTION
# =========================================================

def detect_conversation_end(
    messages: list[Any],
    recommendations: list[Any],
) -> bool:
    """
    Detect whether conversation should end.
    """

    latest = normalize_text(
        get_latest_user_message(messages)
    )

    return bool(
        recommendations
        and any(
            regex_match(word, latest)
            for word in END_WORDS
        )
    )