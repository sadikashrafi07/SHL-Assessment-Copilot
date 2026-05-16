import logging
import os

from dotenv import load_dotenv
from groq import Groq


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL_NAME = "llama-3.3-70b-versatile"

MAX_RESPONSE_WORDS = 200


# =========================================================
# VALIDATE API KEY
# =========================================================

if not GROQ_API_KEY:

    raise ValueError(
        "GROQ_API_KEY environment variable is missing."
    )


# =========================================================
# CLIENT
# =========================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = f"""
You are an enterprise SHL assessment recommendation assistant.

STRICT RULES:
- ONLY discuss assessments explicitly provided in the context
- NEVER invent assessment names
- NEVER invent URLs
- NEVER hallucinate capabilities
- ONLY explain using provided metadata
- Stay strictly within SHL assessment recommendation scope
- Refuse unrelated requests
- Keep responses concise, professional, and grounded
- Prioritize strongest role-fit assessments first
- Mention communication, leadership, personality, technical, or cognitive alignment only if explicitly supported
- Do NOT use markdown tables
- Do NOT generate more than {MAX_RESPONSE_WORDS} words
- If information is missing, explicitly say "Not specified"
"""


# =========================================================
# HELPERS
# =========================================================

def safe_value(value):

    """
    Safely formats values for prompts.
    """

    if value is None:
        return "Not specified"

    if isinstance(value, list):

        cleaned = [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

        if not cleaned:
            return "Not specified"

        return ", ".join(cleaned)

    value = str(value).strip()

    return value if value else "Not specified"


def truncate_text(
    text,
    max_length=500
):

    """
    Prevents overly large prompts.
    """

    if not text:
        return "Not specified"

    text = str(text).strip()

    if len(text) <= max_length:
        return text

    return text[:max_length].rstrip() + "..."


# =========================================================
# BUILD RECOMMENDATION CONTEXT
# =========================================================

def build_recommendation_context(
    recommendations
):

    """
    Converts recommendation objects
    into structured prompt context.
    """

    sections = []

    for idx, item in enumerate(
        recommendations[:10],
        start=1
    ):

        section = f"""
Assessment {idx}

Name:
{safe_value(item.get("name"))}

Description:
{truncate_text(
    safe_value(
        item.get("description")
    ),
    600
)}

Test Type:
{safe_value(item.get("test_type"))}

Technical Skills:
{safe_value(
    item.get("technical_skills")
)}

Communication Skills:
{safe_value(
    item.get("communication_skills")
)}

Leadership Traits:
{safe_value(
    item.get("leadership_traits")
)}

Personality Traits:
{safe_value(
    item.get("personality_traits")
)}

Cognitive Traits:
{safe_value(
    item.get("cognitive_traits")
)}

Job Levels:
{safe_value(item.get("job_levels"))}

Duration:
{safe_value(item.get("duration"))}

Adaptive:
{safe_value(item.get("adaptive"))}

Remote:
{safe_value(item.get("remote"))}

URL:
{safe_value(item.get("url"))}
"""

        sections.append(
            section.strip()
        )

    return "\n\n".join(sections)


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    user_query,
    recommendations,
    context,
    intent
):

    """
    Builds the final grounded prompt.
    """

    recommendation_context = (
        build_recommendation_context(
            recommendations
        )
    )

    prompt = f"""
Hiring Requirement:
{safe_value(user_query)}

Detected Intent:
{safe_value(intent)}

Extracted Context:

Roles:
{safe_value(context.get("roles"))}

Seniority:
{safe_value(context.get("seniority"))}

Skills:
{safe_value(context.get("skills"))}

Assessment Types:
{safe_value(
    context.get("assessment_types")
)}

Leadership Required:
{safe_value(
    context.get("leadership_required")
)}

Communication Required:
{safe_value(
    context.get("communication_required")
)}

Personality Required:
{safe_value(
    context.get("personality_required")
)}

Cognitive Required:
{safe_value(
    context.get("cognitive_required")
)}

Available Assessments:
{recommendation_context}

TASK:
Generate a concise and professional recommendation response.

Requirements:
- Mention strongest assessment first
- Explain fit briefly
- Mention technical/personality/communication/cognitive alignment only if relevant
- Stay grounded strictly in provided assessments
- Never invent assessment details
- Keep response under {MAX_RESPONSE_WORDS} words
"""

    return prompt.strip()


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def fallback_response(
    recommendations
):

    """
    Safe deterministic fallback response.
    """

    if not recommendations:

        return (
            "I could not find strong matching "
            "SHL assessments for the provided "
            "hiring requirements."
        )

    names = [

        item.get("name")

        for item in recommendations[:3]

        if item.get("name")
    ]

    if not names:

        return (
            "Relevant SHL assessments were "
            "identified, but assessment names "
            "were unavailable."
        )

    joined = ", ".join(names)

    return (
        f"I identified several relevant SHL "
        f"assessments including {joined}. "
        f"These assessments align with the "
        f"hiring requirements provided."
    )


# =========================================================
# RESPONSE CLEANER
# =========================================================

def clean_response(content):

    """
    Basic response sanitation.
    """

    if not content:
        return ""

    content = content.strip()

    # Remove excessive blank lines
    lines = [

        line.strip()

        for line in content.splitlines()

        if line.strip()
    ]

    cleaned = "\n".join(lines)

    return cleaned[:3000]


# =========================================================
# MAIN GENERATION
# =========================================================

def generate_llm_response(
    user_query,
    recommendations,
    context,
    intent
):

    """
    Generates grounded recommendation response.
    """

    try:

        # =====================================
        # EMPTY RESULTS
        # =====================================

        if not recommendations:

            logger.warning(
                "No recommendations available."
            )

            return fallback_response([])

        # =====================================
        # BUILD PROMPT
        # =====================================

        prompt = build_prompt(
            user_query=user_query,
            recommendations=recommendations,
            context=context,
            intent=intent
        )

        logger.info(
            "Generating LLM response..."
        )

        # =====================================
        # LLM REQUEST
        # =====================================

        response = (
            client.chat.completions.create(

                model=MODEL_NAME,

                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.1,

                max_tokens=220,

                top_p=0.9
            )
        )

        # =====================================
        # EXTRACT RESPONSE
        # =====================================

        content = (
            response.choices[0]
            .message
            .content
        )

        cleaned_content = clean_response(
            content
        )

        # =====================================
        # EMPTY SAFETY
        # =====================================

        if not cleaned_content:

            logger.warning(
                "Empty LLM response received."
            )

            return fallback_response(
                recommendations
            )

        return cleaned_content

    except Exception as error:

        logger.exception(
            f"LLM generation failed: {error}"
        )

        return fallback_response(
            recommendations
        )