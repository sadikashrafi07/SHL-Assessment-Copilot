# =========================================================
# app/services/conversation.py
# Production-Grade Conversation Understanding Engine
# FULLY FIXED ENTERPRISE VERSION
# =========================================================

from __future__ import annotations

import logging
import re

from functools import lru_cache

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Pattern
from typing import Set

from app.utils.helpers import normalize

logger = logging.getLogger(__name__)

# =========================================================
# CONSTANTS
# =========================================================

COMPARISON_WORDS: Set[str] = {
    "compare",
    "comparison",
    "difference",
    "versus",
    "vs",
    "better than",
    "alternative",
    "alternative to",
    "which is better",
}

REFINEMENT_WORDS: Set[str] = {
    "actually",
    "instead",
    "update",
    "modify",
    "change",
    "replace",
    "refine",
    "narrow",
    "filter",
}

END_WORDS: Set[str] = {
    "thanks",
    "thank you",
    "bye",
    "done",
    "goodbye",
    "perfect",
    "great",
    "resolved",
}

# =========================================================
# GREETING WORDS
# =========================================================

GREETING_WORDS: Set[str] = {
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

HELP_WORDS: Set[str] = {
    "help",
    "what can you do",
    "how can you help",
    "features",
    "capabilities",
    "assist",
}

# =========================================================
# STRONG OFFTOPIC FILTERS
# =========================================================

OFFTOPIC_WORDS: Set[str] = {

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

DOMAIN_KEYWORDS: Set[str] = {

    # Hiring
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

    # Assessment Types
    "technical assessment",
    "coding assessment",
    "personality assessment",
    "leadership assessment",
    "cognitive assessment",
    "aptitude test",

    # Roles
    "developer",
    "engineer",
    "manager",
    "architect",
    "analyst",
    "designer",

    # Skills
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

ROLE_PATTERNS: List[str] = sorted(
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

SENIORITY_PATTERNS: List[str] = [
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

ASSESSMENT_TYPES: List[str] = [
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

SKILL_PATTERNS: List[str] = sorted(
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

@lru_cache(maxsize=4096)
def build_pattern(term: str) -> Pattern[str]:
    """
    Cached safe whole-word regex pattern.
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

    normalized_text = normalize_text(text)

    return bool(
        build_pattern(term).search(
            normalized_text
        )
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

    normalized = normalize(str(text))

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()

# =========================================================
# EXTRACTION HELPERS
# =========================================================

def deduplicate(
    items: List[str],
) -> List[str]:
    """
    Deterministic deduplication.
    """

    seen: Set[str] = set()

    result: List[str] = []

    for item in items:

        value = normalize_text(item)

        if value and value not in seen:

            seen.add(value)

            result.append(value)

    return result


def extract_roles(
    text: str,
) -> List[str]:
    """
    Extract role mentions.
    """

    normalized_text = normalize_text(text)

    found: List[str] = []

    for role in ROLE_PATTERNS:

        if regex_match(
            role,
            normalized_text,
        ):
            found.append(role)

    return deduplicate(found)


def extract_seniority(
    text: str,
) -> Optional[str]:
    """
    Extract seniority level.
    """

    normalized_text = normalize_text(text)

    for level in SENIORITY_PATTERNS:

        if regex_match(
            level,
            normalized_text,
        ):
            return level

    return None


def extract_assessment_types(
    text: str,
) -> List[str]:
    """
    Extract assessment types.
    """

    normalized_text = normalize_text(text)

    found: List[str] = []

    for assessment_type in ASSESSMENT_TYPES:

        if regex_match(
            assessment_type,
            normalized_text,
        ):
            found.append(
                assessment_type
            )

    return deduplicate(found)


def extract_skills(
    text: str,
) -> List[str]:
    """
    Extract technical + professional skills.
    """

    normalized_text = normalize_text(text)

    found: List[str] = []

    for skill in SKILL_PATTERNS:

        if regex_match(
            skill,
            normalized_text,
        ):
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

    normalized_text = normalize_text(text)

    if not normalized_text:
        return False

    # Greetings allowed
    if any(
        regex_match(word, normalized_text)
        for word in GREETING_WORDS
    ):
        return True

    # Help allowed
    if any(
        regex_match(word, normalized_text)
        for word in HELP_WORDS
    ):
        return True

    # Strong offtopic detection
    offtopic_hits = sum(
        1
        for word in OFFTOPIC_WORDS
        if regex_match(word, normalized_text)
    )

    if offtopic_hits >= 2:
        return False

    role_matches = extract_roles(
        normalized_text
    )

    skill_matches = extract_skills(
        normalized_text
    )

    assessment_matches = (
        extract_assessment_types(
            normalized_text
        )
    )

    keyword_matches = any(
        regex_match(word, normalized_text)
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
    messages: List[Any],
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

        if normalize_text(role_value) == "user":
            return str(content or "")

    return ""


def build_conversation_text(
    messages: List[Any],
) -> str:
    """
    Build normalized conversation text.
    """

    parts: List[str] = []

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
    messages: List[Any],
) -> str:
    """
    Detect conversational intent safely.
    """

    latest = normalize_text(
        get_latest_user_message(
            messages
        )
    )

    if not latest:
        return "recommendation"

    # Greeting
    if any(
        regex_match(word, latest)
        for word in GREETING_WORDS
    ):
        return "greeting"

    # Help
    if any(
        regex_match(word, latest)
        for word in HELP_WORDS
    ):
        return "help"

    # Offtopic
    if not is_relevant_query(latest):
        return "offtopic"

    # Comparison
    if (
        " vs " in latest
        or any(
            regex_match(word, latest)
            for word in COMPARISON_WORDS
        )
    ):
        return "comparison"

    # Refinement
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
) -> Optional[int]:
    """
    Extract duration limits.
    """

    normalized_text = normalize_text(text)

    patterns = [
        r"under\s+(\d+)\s*(mins|minutes)",
        r"less than\s+(\d+)\s*(mins|minutes)",
        r"within\s+(\d+)\s*(mins|minutes)",
        r"(\d+)\s*(mins|minutes)\s*max",
        r"max\s*(\d+)\s*(mins|minutes)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            normalized_text,
        )

        if match:
            try:
                return int(match.group(1))
            except (
                TypeError,
                ValueError,
            ):
                continue

    return None


def extract_experience(
    text: str,
) -> Optional[str]:
    """
    Extract years of experience.
    """

    normalized_text = normalize_text(text)

    match = re.search(
        r"(\d+)\+?\s*(years|yrs|year)",
        normalized_text,
    )

    if match:
        return match.group(1)

    return None


def extract_comparison_targets(
    text: str,
) -> List[str]:
    """
    Extract comparison targets.
    """

    normalized_text = normalize_text(text)

    if " vs " in normalized_text:

        return deduplicate(
            [
                item.strip()
                for item in normalized_text.split(" vs ")
                if item.strip()
            ]
        )[:2]

    match = re.search(
        r"compare\s+(.+?)\s+and\s+(.+)",
        normalized_text,
    )

    if match:

        return deduplicate(
            [
                match.group(1),
                match.group(2),
            ]
        )[:2]

    return []

# =========================================================
# CONTEXT EXTRACTION
# =========================================================

def extract_context(
    messages: List[Any],
) -> Dict[str, Any]:
    """
    Extract structured conversation context.
    """

    text = build_conversation_text(
        messages
    )

    latest_message = normalize_text(
        get_latest_user_message(
            messages
        )
    )

    intent = detect_intent(messages)

    roles = extract_roles(text)

    skills = extract_skills(text)

    assessment_types = (
        extract_assessment_types(
            text
        )
    )

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

    context: Dict[str, Any] = {

        "roles":
            deduplicate(roles),

        "seniority":
            extract_seniority(text),

        "skills":
            deduplicate(skills),

        "assessment_types":
            deduplicate(
                assessment_types
            ),

        "duration_limit":
            extract_duration_constraint(
                text
            ),

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
    context: Dict[str, Any],
    messages: List[Any],
) -> Dict[str, Any]:
    """
    Determine whether clarification is needed.
    """

    intent = context.get(
        "intent"
    )

    if intent in {
        "offtopic",
        "greeting",
        "help",
    }:

        return {
            "needed": False,
            "missing_fields": [],
            "offtopic":
                intent == "offtopic",
        }

    has_signal = any(
        [
            context.get("roles"),
            context.get("skills"),
            context.get(
                "assessment_types"
            ),
            context.get(
                "leadership_required"
            ),
            context.get(
                "communication_required"
            ),
            context.get(
                "cognitive_required"
            ),
            context.get(
                "personality_required"
            ),
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
    missing_fields: List[str],
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

    if "role" in missing_fields:

        return (
            "Could you share the target role, "
            "seniority level, and key technical "
            "or professional skills you want "
            "to evaluate?"
        )

    return (
        "Please provide additional hiring "
        "requirements or assessment preferences."
    )

# =========================================================
# SEARCH QUERY
# =========================================================

def build_search_query(
    context: Dict[str, Any],
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

    parts: List[str] = []

    parts.extend(
        context.get("roles", [])
    )

    seniority = context.get(
        "seniority"
    )

    if seniority:
        parts.append(seniority)

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

    experience = context.get(
        "experience"
    )

    if experience:
        parts.append(
            f"{experience} years"
        )

    query = normalize_text(
        " ".join(
            deduplicate(parts)
        )
    )

    logger.info(
        "Final search query: %s",
        query,
    )

    return query

# =========================================================
# END DETECTION
# =========================================================

def detect_conversation_end(
    messages: List[Any],
    recommendations: List[Any],
) -> bool:
    """
    Detect whether conversation should end.
    """

    latest = normalize_text(
        get_latest_user_message(
            messages
        )
    )

    return bool(
        recommendations
        and any(
            regex_match(word, latest)
            for word in END_WORDS
        )
    )

# =========================================================
# DEBUG
# =========================================================

if __name__ == "__main__":

    sample_messages = [
        {
            "role": "user",
            "content": (
                "Need assessment for senior "
                "backend python developer "
                "with leadership and "
                "communication skills "
                "under 45 minutes"
            ),
        }
    ]

    extracted = extract_context(
        sample_messages
    )

    print(extracted)

    print(
        build_search_query(
            extracted
        )
    )