# =========================================================
# app/routes/chat.py
# Production-Grade Enterprise Chat Endpoint
# FULLY FIXED ENTERPRISE VERSION
# =========================================================

from __future__ import annotations

import logging
import time
import traceback
from typing import Any
from typing import List

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    Recommendation,
)

from app.services.guardrails import (
    is_safe_query,
    refusal_response,
)

from app.services.conversation import (
    build_search_query,
    detect_conversation_end,
    detect_intent,
    extract_context,
    generate_clarification_question,
    get_latest_user_message,
    should_ask_clarification,
)

from app.services.recommendation import (
    generate_recommendations,
)

from app.services.retrieval import (
    search_assessments,
)

from app.services.comparison import (
    compare_assessments,
)

from app.services.llm import (
    generate_llm_response,
)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(__name__)

# =========================================================
# ROUTER
# =========================================================

router = APIRouter()

# =========================================================
# CONSTANTS
# =========================================================

GREETING_WORDS = {
    "hi",
    "hii",
    "hiii",
    "hello",
    "hey",
    "heyy",
    "hy",
    "hyy",
    "yo",
    "hola",
    "sup",

    "good morning",
    "good afternoon",
    "good evening",
    "good night",
}

# =========================================================
# HEALTH
# =========================================================


@router.get("/health")
async def health() -> dict:

    return {
        "status": "ok",
    }


# =========================================================
# SAFE FLOAT
# =========================================================


def safe_float(
    value: Any,
    default: float | None = None,
) -> float | None:

    try:

        if value is None:
            return default

        value = float(value)

        if value < 0:
            return default

        if value > 1:
            return 1.0

        return round(value, 4)

    except Exception:

        return default


# =========================================================
# NORMALIZE TEST TYPE
# =========================================================


def normalize_test_type(
    value: Any,
) -> str:

    allowed = {
        "K",
        "P",
        "A",
        "S",
        "L",
    }

    value = str(value or "K").upper().strip()

    if value not in allowed:
        return "K"

    return value


# =========================================================
# NORMALIZE STRING LIST
# =========================================================


def normalize_string_list(
    value: Any,
) -> list[str]:

    if not value:
        return []

    if isinstance(value, str):

        value = [value]

    if not isinstance(value, list):
        return []

    cleaned = []

    for item in value:

        item = str(item).strip()

        if item:
            cleaned.append(item)

    return cleaned


# =========================================================
# GREETING CHECK
# =========================================================


def is_greeting_message(
    message: str,
) -> bool:

    """
    Detect casual greeting messages safely.
    Supports:
    - hi
    - hello there
    - hey buddy
    - good morning
    - hii
    """

    message = str(
        message or ""
    ).strip().lower()

    if not message:
        return False

    # =====================================================
    # EXACT MATCH
    # =====================================================

    if message in GREETING_WORDS:
        return True

    # =====================================================
    # STARTS WITH GREETING
    # =====================================================

    for greeting in GREETING_WORDS:

        if message.startswith(
            greeting + " "
        ):
            return True

    # =====================================================
    # SHORT CASUAL GREETINGS
    # =====================================================

    short_patterns = [
        "hello there",
        "hy",
        "hyy",
        "heyy",
        "hiii",
        "yo bro",
        "hey shl",
        "hi shl",
        "hello shl",
        "hey there",
        "hi there",
        "hey buddy",
        "hi buddy",
        "hello buddy",
        "hello shl",
        "hi shl",
    ]

    return message in short_patterns


# =========================================================
# GREETING RESPONSE
# =========================================================

def build_greeting_response() -> str:

    return (
        "Hello! 👋\n\n"
        "I am your SHL Assessment Copilot.\n\n"
        "I can help you with:\n"
        "• SHL assessment recommendations\n"
        "• Technical hiring evaluations\n"
        "• Personality and leadership assessments\n"
        "• Cognitive and aptitude testing\n"
        "• Role-based assessment selection\n"
        "• Assessment comparisons\n\n"
        "You can ask things like:\n"
        "• Python developer assessment\n"
        "• Leadership test for engineering managers\n"
        "• Java backend hiring assessment\n"
        "• Cognitive test for analysts\n"
        "• Compare coding vs aptitude assessments\n\n"
        "How can I help you today?"
    )

# =========================================================
# NORMALIZE RECOMMENDATIONS
# =========================================================


def normalize_recommendations(
    recommendations: list[Any],
) -> List[Recommendation]:

    """
    Convert recommendation output into
    strict Recommendation schema safely.
    """

    normalized: List[Recommendation] = []

    seen_names = set()

    for item in recommendations:

        try:

            # =====================================================
            # ALREADY MODEL
            # =====================================================

            if isinstance(
                item,
                Recommendation,
            ):

                normalized_name = (
                    item.name.lower().strip()
                )

                if normalized_name in seen_names:
                    continue

                seen_names.add(
                    normalized_name
                )

                normalized.append(item)

                continue

            # =====================================================
            # INVALID TYPE
            # =====================================================

            if not isinstance(item, dict):

                logger.warning(
                    "Skipping invalid recommendation type: %s",
                    type(item),
                )

                continue

            # =====================================================
            # REQUIRED NAME
            # =====================================================

            name = str(
                item.get("name", "")
            ).strip()

            if not name:
                continue

            normalized_name = (
                name.lower()
            )

            if normalized_name in seen_names:
                continue

            seen_names.add(
                normalized_name
            )

            # =====================================================
            # BUILD RECOMMENDATION
            # =====================================================

            recommendation = Recommendation(

                name=name,

                url=item.get("url"),

                test_type=normalize_test_type(
                    item.get("test_type")
                ),

                description=str(
                    item.get(
                        "description",
                        "",
                    )
                ).strip(),

                score=safe_float(
                    item.get("score"),
                    0.0,
                ),

                confidence=safe_float(
                    item.get("confidence"),
                    0.0,
                ),

                recommendation_strength=str(
                    item.get(
                        "recommendation_strength",
                        "medium",
                    )
                ),

                explanation=str(
                    item.get(
                        "explanation",
                        "",
                    )
                ).strip(),

                matched_roles=normalize_string_list(
                    item.get(
                        "matched_roles",
                    )
                ),

                matched_domains=normalize_string_list(
                    item.get(
                        "matched_domains",
                    )
                ),

                matched_competencies=normalize_string_list(
                    item.get(
                        "matched_competencies",
                    )
                ),

                domains=normalize_string_list(
                    item.get(
                        "domains",
                    )
                ),

                roles=normalize_string_list(
                    item.get(
                        "roles",
                    )
                ),

                job_levels=normalize_string_list(
                    item.get(
                        "job_levels",
                    )
                ),

                languages=normalize_string_list(
                    item.get(
                        "languages",
                    )
                ),

                duration=item.get(
                    "duration"
                ),

                remote=bool(
                    item.get(
                        "remote",
                        False,
                    )
                ),

                adaptive=bool(
                    item.get(
                        "adaptive",
                        False,
                    )
                ),

                retrieval_metadata=item.get(
                    "retrieval_metadata",
                    {},
                ),
            )

            normalized.append(
                recommendation
            )

        except Exception as error:

            logger.exception(
                "Recommendation normalization failed: %s",
                error,
            )

            continue

    return normalized


# =========================================================
# SAFE CHAT RESPONSE
# =========================================================


def build_chat_response(
    reply: str,
    recommendations: list[Recommendation],
    end_of_conversation: bool = False,
) -> ChatResponse:

    return ChatResponse(
        reply=reply,
        recommendations=recommendations,
        end_of_conversation=end_of_conversation,
    )


# =========================================================
# OFFTOPIC RESPONSE
# =========================================================


def build_offtopic_response() -> str:

    return (
        "I can assist only with SHL assessment and "
        "hiring-related queries.\n\n"
        "Supported areas:\n"
        "• Technical assessments\n"
        "• Personality assessments\n"
        "• Leadership evaluations\n"
        "• Cognitive testing\n"
        "• Hiring recommendations\n"
        "• Assessment comparisons\n\n"
        "Example queries:\n"
        "• Python developer assessment\n"
        "• Leadership test for managers\n"
        "• Cognitive assessment for analysts\n"
        "• Java backend developer hiring test"
    )


# =========================================================
# EMPTY SEARCH RESPONSE
# =========================================================


def build_empty_search_response() -> str:

    return (
        "I could not identify enough hiring or "
        "assessment-related information.\n\n"
        "Please include:\n"
        "• Target role\n"
        "• Skills\n"
        "• Seniority\n"
        "• Assessment type\n\n"
        "Example:\n"
        "'Senior Python Developer technical assessment'"
    )


# =========================================================
# CHAT ENDPOINT
# =========================================================


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
) -> ChatResponse:

    start_time = time.perf_counter()

    logger.info(
        "CHAT REQUEST STARTED"
    )

    try:

        # =====================================================
        # VALIDATE REQUEST
        # =====================================================

        if not request.messages:

            return build_chat_response(
                reply=(
                    "Please provide a hiring "
                    "requirement or assessment query."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # USER MESSAGE
        # =====================================================

        latest_user_message = (
            get_latest_user_message(
                request.messages
            )
        )

        latest_user_message = str(
            latest_user_message or ""
        ).strip()

        logger.info(
            "Latest user message: %s",
            latest_user_message,
        )

        # =====================================================
        # EMPTY USER MESSAGE
        # =====================================================

        if not latest_user_message:

            return build_chat_response(
                reply=(
                    "Please provide a valid "
                    "job requirement or hiring query."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # GREETING HANDLING
        # =====================================================

        if is_greeting_message(
            latest_user_message
        ):

            logger.info(
                "Greeting message detected"
            )

            return build_chat_response(
                reply=build_greeting_response(),
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # SAFETY CHECK
        # =====================================================

        if not is_safe_query(
            latest_user_message
        ):

            logger.warning(
                "Unsafe query blocked"
            )

            return build_chat_response(
                reply=refusal_response(),
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # DETECT INTENT
        # =====================================================

        intent = detect_intent(
            request.messages
        )

        logger.info(
            "Intent detected: %s",
            intent,
        )

        # =====================================================
        # OFFTOPIC
        # =====================================================

        if intent == "offtopic":

            return build_chat_response(
                reply=build_offtopic_response(),
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # EXTRACT CONTEXT
        # =====================================================

        context = extract_context(
            request.messages
        )

        logger.info(
            "Extracted context: %s",
            context,
        )

        # =====================================================
        # CLARIFICATION
        # =====================================================

        clarification = (
            should_ask_clarification(
                context=context,
                messages=request.messages,
            )
        )

        clarification_needed = (
            clarification.get(
                "needed",
                False,
            )
        )

        clarification_offtopic = (
            clarification.get(
                "offtopic",
                False,
            )
        )

        # =====================================================
        # OFFTOPIC CLARIFICATION
        # =====================================================

        if clarification_offtopic:

            return build_chat_response(
                reply=build_offtopic_response(),
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # NORMAL CLARIFICATION
        # =====================================================

        if clarification_needed:

            question = (
                generate_clarification_question(
                    clarification.get(
                        "missing_fields",
                        [],
                    )
                )
            )

            return build_chat_response(
                reply=question,
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # BUILD SEARCH QUERY
        # =====================================================

        search_query = (
            build_search_query(
                context
            )
        )

        search_query = str(
            search_query or ""
        ).strip()

        logger.info(
            "Search query: %s",
            search_query,
        )

        # =====================================================
        # EMPTY SEARCH QUERY
        # =====================================================

        if not search_query:

            return build_chat_response(
                reply=build_empty_search_response(),
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # RETRIEVAL
        # =====================================================

        logger.info(
            "Starting retrieval"
        )

        raw_results = await run_in_threadpool(
            search_assessments,
            search_query,
        )

        raw_results = raw_results or []

        logger.info(
            "Retrieved %s raw results",
            len(raw_results),
        )

        # =====================================================
        # NO RESULTS
        # =====================================================

        if not raw_results:

            return build_chat_response(
                reply=(
                    "I could not find sufficiently "
                    "relevant SHL assessments for "
                    "this hiring requirement."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # GENERATE RECOMMENDATIONS
        # =====================================================

        recommendations = await run_in_threadpool(
            generate_recommendations,
            raw_results,
            search_query,
            context,
        )

        recommendations = recommendations or []

        logger.info(
            "Generated %s recommendations",
            len(recommendations),
        )

        # =====================================================
        # NORMALIZE
        # =====================================================

        recommendations = (
            normalize_recommendations(
                recommendations
            )
        )

        logger.info(
            "Normalized %s recommendations",
            len(recommendations),
        )

        # =====================================================
        # EMPTY RESULTS
        # =====================================================

        if not recommendations:

            return build_chat_response(
                reply=(
                    "I found assessment matches, "
                    "but none passed final validation."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =====================================================
        # COMPARISON MODE
        # =====================================================

        if intent == "comparison":

            logger.info(
                "Comparison mode activated"
            )

            comparison_reply = (
                await run_in_threadpool(
                    compare_assessments,
                    recommendations,
                )
            )

            return build_chat_response(
                reply=comparison_reply,
                recommendations=recommendations,
                end_of_conversation=False,
            )

        # =====================================================
        # GENERATE LLM RESPONSE
        # =====================================================

        try:

            logger.info(
                "Generating LLM response"
            )

            reply = await run_in_threadpool(
                generate_llm_response,
                latest_user_message,
                recommendations,
                context,
                intent,
            )

            if not reply:

                raise ValueError(
                    "Empty LLM response"
                )

            reply = str(reply).strip()

        except Exception as error:

            logger.exception(
                "LLM generation failed: %s",
                error,
            )

            top_names = [
                item.name
                for item in recommendations[:3]
            ]

            reply = (
                "I found relevant SHL assessments including: "
                f"{', '.join(top_names)}."
            )

        # =====================================================
        # END DETECTION
        # =====================================================

        end_of_conversation = (
            detect_conversation_end(
                request.messages,
                recommendations,
            )
        )

        # =====================================================
        # RESPONSE TIME
        # =====================================================

        response_time_ms = round(
            (
                time.perf_counter()
                - start_time
            )
            * 1000,
            2,
        )

        logger.info(
            "CHAT REQUEST COMPLETED"
        )

        logger.info(
            "Response time: %sms",
            response_time_ms,
        )

        # =====================================================
        # FINAL RESPONSE
        # =====================================================

        return build_chat_response(
            reply=reply,
            recommendations=recommendations,
            end_of_conversation=end_of_conversation,
        )

    except HTTPException:

        raise

    except Exception as error:

        logger.error(
            "CHAT ENDPOINT CRASHED"
        )

        logger.error(
            traceback.format_exc()
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Internal server error occurred "
                "while processing request."
            ),
        ) from error