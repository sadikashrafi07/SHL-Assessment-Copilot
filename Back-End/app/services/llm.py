# =========================================================
# app/services/llm.py
# ENTERPRISE SHL LLM ENGINE v2 PRODUCTION FINAL
# FULLY FIXED + RATE LIMIT SAFE + LOW TOKEN
# STRICT GROUNDING + ZERO HALLUCINATION
# NO ARCHITECTURE CHANGES
# ASSIGNMENT READY
# =========================================================

from __future__ import annotations

import logging
import os
import random
import re
import time

from typing import Any

from dotenv import load_dotenv
from groq import Groq
from groq import APIError
from groq import RateLimitError

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(__name__)

# =========================================================
# CONFIG
# =========================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile",
)

MAX_RESPONSE_WORDS = 220

MAX_RECOMMENDATIONS_IN_PROMPT = 4

MAX_DESCRIPTION_LENGTH = 260

MAX_EXPLANATION_LENGTH = 180

MAX_RETRIES = 2

REQUEST_TIMEOUT = 18

SAFE_FALLBACK_MODE = os.getenv(
    "SAFE_FALLBACK_MODE",
    "false",
).lower() == "true"

# =========================================================
# VALIDATE
# =========================================================

if not GROQ_API_KEY:

    raise ValueError(
        "GROQ_API_KEY environment variable is missing."
    )

# =========================================================
# CLIENT
# =========================================================

client = Groq(
    api_key=GROQ_API_KEY,
)

# =========================================================
# TEST TYPE LABELS
# =========================================================

TEST_TYPE_LABELS = {

    "K":
        "Technical Assessment",

    "A":
        "Cognitive Assessment",

    "P":
        "Behavioral Assessment",

    "S":
        "Situational Assessment",

    "L":
        "Leadership Assessment",
}

# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = f"""
You are an enterprise SHL assessment recommendation assistant.

STRICT RULES:
- ONLY use assessments explicitly provided
- NEVER invent assessment names
- NEVER invent URLs
- NEVER invent metadata
- NEVER hallucinate adaptive or remote support
- NEVER recommend irrelevant assessments
- Keep explanations concise and role-specific
- Focus on strongest technical and competency alignment
- Avoid repetitive wording
- Avoid generic explanations
- Mention leadership or cognitive fit ONLY if metadata supports it
- Never use markdown tables
- Never mention internal scores
- Output must remain under {MAX_RESPONSE_WORDS} words
- Sound professional and enterprise-grade
"""

# =========================================================
# SAFE ACCESS
# =========================================================

def safe_get(
    item: Any,
    key: str,
    default: Any = None,
) -> Any:

    if item is None:
        return default

    if isinstance(item, dict):
        return item.get(
            key,
            default,
        )

    if hasattr(item, "model_dump"):

        try:
            return item.model_dump().get(
                key,
                default,
            )

        except Exception:
            pass

    if hasattr(item, "dict"):

        try:
            return item.dict().get(
                key,
                default,
            )

        except Exception:
            pass

    return getattr(
        item,
        key,
        default,
    )

# =========================================================
# SAFE STRING
# =========================================================

def safe_str(
    value: Any,
    default: str = "Not specified",
) -> str:

    if value is None:
        return default

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, list):

        cleaned = [
            str(v).strip()
            for v in value
            if str(v).strip()
        ]

        if not cleaned:
            return default

        return ", ".join(cleaned)

    value = str(value).strip()

    if not value:
        return default

    return value

# =========================================================
# TRUNCATE
# =========================================================

def truncate(
    text: Any,
    limit: int,
) -> str:

    value = safe_str(text)

    if len(value) <= limit:
        return value

    return (
        value[:limit]
        .rstrip()
        + "..."
    )

# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(
    text: str,
) -> str:

    text = str(text or "")

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()

# =========================================================
# NORMALIZE RECOMMENDATION
# =========================================================

def normalize_recommendation(
    item: Any,
) -> dict[str, Any]:

    test_type = safe_str(
        safe_get(
            item,
            "test_type",
            "K",
        )
    )

    return {

        "name":
            safe_str(
                safe_get(
                    item,
                    "name",
                )
            ),

        "description":
            truncate(
                safe_get(
                    item,
                    "description",
                ),
                MAX_DESCRIPTION_LENGTH,
            ),

        "url":
            safe_str(
                safe_get(
                    item,
                    "url",
                )
            ),

        "test_type":
            test_type,

        "test_type_label":
            TEST_TYPE_LABELS.get(
                test_type,
                "Assessment",
            ),

        "score":
            float(
                safe_get(
                    item,
                    "score",
                    0.0,
                )
                or 0.0
            ),

        "confidence":
            float(
                safe_get(
                    item,
                    "confidence",
                    0.0,
                )
                or 0.0
            ),

        "recommendation_strength":
            safe_str(
                safe_get(
                    item,
                    "recommendation_strength",
                )
            ),

        "explanation":
            truncate(
                safe_get(
                    item,
                    "explanation",
                ),
                MAX_EXPLANATION_LENGTH,
            ),

        "technical_skills":
            truncate(
                safe_get(
                    item,
                    "technical_skills",
                ),
                120,
            ),

        "leadership_traits":
            truncate(
                safe_get(
                    item,
                    "leadership_traits",
                ),
                120,
            ),

        "communication_skills":
            truncate(
                safe_get(
                    item,
                    "communication_skills",
                ),
                120,
            ),

        "job_levels":
            truncate(
                safe_get(
                    item,
                    "job_levels",
                ),
                80,
            ),

        "adaptive":
            safe_str(
                safe_get(
                    item,
                    "adaptive",
                    False,
                )
            ),

        "remote":
            safe_str(
                safe_get(
                    item,
                    "remote",
                    False,
                )
            ),
    }

# =========================================================
# FILTER RECOMMENDATIONS
# =========================================================

def filter_recommendations(
    recommendations: list[Any],
) -> list[dict[str, Any]]:

    cleaned: list[dict[str, Any]] = []

    seen: set[str] = set()

    for item in recommendations:

        normalized = (
            normalize_recommendation(
                item
            )
        )

        name = clean_text(
            normalized["name"]
        ).lower()

        if (
            not name
            or name == "not specified"
        ):
            continue

        if name in seen:
            continue

        seen.add(name)

        cleaned.append(normalized)

    cleaned.sort(
        key=lambda x: (
            x["confidence"],
            x["score"],
        ),
        reverse=True,
    )

    return cleaned[
        :MAX_RECOMMENDATIONS_IN_PROMPT
    ]

# =========================================================
# BUILD CONTEXT
# =========================================================

def build_recommendation_context(
    recommendations: list[Any],
) -> str:

    normalized = (
        filter_recommendations(
            recommendations
        )
    )

    sections: list[str] = []

    for idx, item in enumerate(
        normalized,
        start=1,
    ):

        section = f"""
Assessment {idx}

Name:
{item["name"]}

Type:
{item["test_type_label"]}

Description:
{item["description"]}

Explanation:
{item["explanation"]}

Technical Skills:
{item["technical_skills"]}

Leadership Traits:
{item["leadership_traits"]}

Communication Skills:
{item["communication_skills"]}

Job Levels:
{item["job_levels"]}

Adaptive:
{item["adaptive"]}

Remote:
{item["remote"]}

URL:
{item["url"]}
"""

        sections.append(
            clean_text(section)
        )

    return "\n\n".join(sections)

# =========================================================
# BUILD PROMPT
# =========================================================

def build_prompt(
    user_query: str,
    recommendations: list[Any],
    context: dict[str, Any],
    intent: str,
) -> str:

    recommendation_context = (
        build_recommendation_context(
            recommendations
        )
    )

    return f"""
USER REQUIREMENT:
{truncate(user_query, 300)}

INTENT:
{truncate(intent, 120)}

ROLE:
{truncate(context.get("roles"), 120)}

SENIORITY:
{truncate(context.get("seniority"), 80)}

SKILLS:
{truncate(context.get("skills"), 220)}

ASSESSMENT TYPES:
{truncate(context.get("assessment_types"), 120)}

LEADERSHIP REQUIRED:
{safe_str(context.get("leadership_required"))}

COMMUNICATION REQUIRED:
{safe_str(context.get("communication_required"))}

COGNITIVE REQUIRED:
{safe_str(context.get("cognitive_required"))}

AVAILABLE SHL ASSESSMENTS:
{recommendation_context}

TASK:
Recommend the strongest assessments first.
Explain role alignment and skill relevance.
Keep response concise and grounded.
"""

# =========================================================
# FALLBACK RESPONSE
# =========================================================

def fallback_response(
    recommendations: list[Any],
) -> str:

    normalized = (
        filter_recommendations(
            recommendations
        )
    )

    if not normalized:

        return (
            "No highly relevant SHL assessments "
            "were identified for the provided "
            "requirements."
        )

    lines: list[str] = []

    lines.append(
        "Recommended SHL assessments:"
    )

    for item in normalized[:3]:

        explanation = (
            item["explanation"]
            if item["explanation"]
            != "Not specified"
            else item["description"]
        )

        lines.append(
            (
                f"- {item['name']}: "
                f"{truncate(explanation, 140)}"
            )
        )

    return "\n".join(lines)

# =========================================================
# CLEAN RESPONSE
# =========================================================

def clean_response(
    content: str,
) -> str:

    if not content:
        return ""

    content = clean_text(content)

    content = re.sub(
        r"Recommendationstrength\.\w+",
        "",
        content,
        flags=re.IGNORECASE,
    )

    content = re.sub(
        r"TestType\.\w+",
        "",
        content,
        flags=re.IGNORECASE,
    )

    return content[:2800].strip()

# =========================================================
# RETRY SLEEP
# =========================================================

def retry_sleep(
    attempt: int,
) -> None:

    base = (
        1.2
        * (attempt + 1)
    )

    jitter = random.uniform(
        0.2,
        0.8,
    )

    time.sleep(
        base + jitter
    )

# =========================================================
# MAIN
# =========================================================

def generate_llm_response(
    user_query: str,
    recommendations: list[Any],
    context: dict[str, Any],
    intent: str,
) -> str:

    try:

        cleaned_recommendations = (
            filter_recommendations(
                recommendations
            )
        )

        if not cleaned_recommendations:

            logger.warning(
                "No valid recommendations found."
            )

            return fallback_response([])

        # =================================================
        # SAFE FALLBACK MODE
        # =================================================

        if SAFE_FALLBACK_MODE:

            logger.warning(
                "SAFE_FALLBACK_MODE enabled."
            )

            return fallback_response(
                cleaned_recommendations
            )

        prompt = build_prompt(
            user_query=user_query,
            recommendations=cleaned_recommendations,
            context=context,
            intent=intent,
        )

        logger.info(
            "Generating grounded SHL response..."
        )

        # =================================================
        # RETRY LOOP
        # =================================================

        for attempt in range(
            MAX_RETRIES + 1
        ):

            try:

                response = (
                    client.chat.completions.create(

                        model=MODEL_NAME,

                        messages=[

                            {
                                "role": "system",
                                "content": SYSTEM_PROMPT,
                            },

                            {
                                "role": "user",
                                "content": prompt,
                            },
                        ],

                        temperature=0.05,

                        max_tokens=220,

                        top_p=0.85,

                        frequency_penalty=0.15,

                        presence_penalty=0.05,

                        timeout=REQUEST_TIMEOUT,
                    )
                )

                content = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                cleaned = clean_response(
                    content
                )

                if not cleaned:

                    logger.warning(
                        "Received empty LLM response."
                    )

                    return fallback_response(
                        cleaned_recommendations
                    )

                return cleaned

            # =============================================
            # RATE LIMIT
            # =============================================

            except RateLimitError as error:

                logger.exception(
                    "Groq rate limit hit: %s",
                    error,
                )

                if attempt >= MAX_RETRIES:

                    logger.warning(
                        "Using deterministic fallback after rate limit."
                    )

                    return fallback_response(
                        cleaned_recommendations
                    )

                retry_sleep(attempt)

            # =============================================
            # API ERROR
            # =============================================

            except APIError as error:

                logger.exception(
                    "Groq API error: %s",
                    error,
                )

                if attempt >= MAX_RETRIES:

                    return fallback_response(
                        cleaned_recommendations
                    )

                retry_sleep(attempt)

            # =============================================
            # GENERIC FAILURE
            # =============================================

            except Exception as error:

                logger.exception(
                    "LLM generation failure: %s",
                    error,
                )

                if attempt >= MAX_RETRIES:

                    return fallback_response(
                        cleaned_recommendations
                    )

                retry_sleep(attempt)

        # =================================================
        # HARD SAFETY
        # =================================================

        return fallback_response(
            cleaned_recommendations
        )

    except Exception as error:

        logger.exception(
            "Fatal LLM pipeline failure: %s",
            error,
        )

        return fallback_response(
            recommendations
        )