# =========================================================
# app/routes/chat.py
# =========================================================

from __future__ import annotations

import logging
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
)

from app.services.guardrails import (
    is_safe_query,
    refusal_response,
)

from app.services.conversation import (
    detect_intent,
    extract_context,
    build_search_query,
    should_ask_clarification,
    generate_clarification_question,
    get_latest_user_message,
    detect_conversation_end,
)

from app.services.retrieval import (
    search_assessments,
)

from app.services.recommendation import (
    generate_recommendations,
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
# HEALTH CHECK
# =========================================================

@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok"
    }

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

    logger.info("CHAT REQUEST STARTED")

    try:

        # =================================================
        # VALIDATE REQUEST
        # =================================================

        if not request.messages:

            logger.warning(
                "Empty messages payload received"
            )

            return ChatResponse(
                reply=(
                    "Please provide a hiring "
                    "requirement or SHL "
                    "assessment query."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =================================================
        # GET LATEST USER MESSAGE
        # =================================================

        latest_user_message = (
            get_latest_user_message(
                request.messages
            ).strip()
        )

        logger.info(
            "Latest user message: %s",
            latest_user_message,
        )

        if not latest_user_message:

            logger.warning(
                "Latest user message empty"
            )

            return ChatResponse(
                reply=(
                    "Please provide a valid "
                    "hiring requirement."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =================================================
        # SAFETY CHECK
        # =================================================

        if not is_safe_query(
            latest_user_message
        ):

            logger.warning(
                "Unsafe query blocked"
            )

            return ChatResponse(
                reply=refusal_response(),
                recommendations=[],
                end_of_conversation=False,
            )

        # =================================================
        # INTENT DETECTION
        # =================================================

        intent = detect_intent(
            request.messages
        )

        logger.info(
            "Detected intent: %s",
            intent,
        )

        # =================================================
        # OFFTOPIC HANDLING
        # =================================================

        if intent == "offtopic":

            logger.info(
                "Handled off-topic request"
            )

            return ChatResponse(
                reply=(
                    "I can help with SHL "
                    "assessment recommendations, "
                    "candidate evaluation, "
                    "and assessment comparisons."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =================================================
        # CONTEXT EXTRACTION
        # =================================================

        context = extract_context(
            request.messages
        )

        logger.info(
            "Extracted context: %s",
            context,
        )

        # =================================================
        # CLARIFICATION CHECK
        # =================================================

        clarification = (
            should_ask_clarification(
                context=context,
                messages=request.messages,
            )
        )

        if clarification.get(
            "needed",
            False,
        ):

            has_role = bool(
                context.get("roles")
            )

            has_skills = bool(
                context.get("skills")
            )

            has_focus = any([
                context.get(
                    "leadership_required"
                ),
                context.get(
                    "communication_required"
                ),
                context.get(
                    "personality_required"
                ),
                context.get(
                    "cognitive_required"
                ),
            ])

            enough_context = any([
                has_role,
                has_skills,
                has_focus,
            ])

            if not enough_context:

                logger.info(
                    "Clarification required"
                )

                question = (
                    generate_clarification_question(
                        clarification.get(
                            "missing_fields",
                            [],
                        )
                    )
                )

                return ChatResponse(
                    reply=question,
                    recommendations=[],
                    end_of_conversation=False,
                )

        # =================================================
        # BUILD SEARCH QUERY
        # =================================================

        search_query = (
            build_search_query(
                context
            )
        )

        logger.info(
            "Search query: %s",
            search_query,
        )

        if not search_query.strip():

            logger.warning(
                "Generated empty search query"
            )

            return ChatResponse(
                reply=(
                    "Please provide more details "
                    "about the role, required skills, "
                    "or assessment focus."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =================================================
        # RETRIEVAL
        # =================================================

        logger.info(
            "Starting assessment retrieval"
        )

        raw_results = await run_in_threadpool(
            search_assessments,
            search_query,
        )

        raw_results = raw_results or []

        logger.info(
            "Retrieved %s candidates",
            len(raw_results),
        )

        if not raw_results:

            logger.warning(
                "No retrieval results found"
            )

            return ChatResponse(
                reply=(
                    "I could not find sufficiently "
                    "relevant SHL assessments."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =================================================
        # RECOMMENDATIONS
        # =================================================

        logger.info(
            "Generating recommendations"
        )

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

        if not recommendations:

            logger.warning(
                "No valid recommendations generated"
            )

            return ChatResponse(
                reply=(
                    "I found possible matches, "
                    "but none passed final validation."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =================================================
        # COMPARISON MODE
        # =================================================

        if intent == "comparison":

            logger.info(
                "Running comparison mode"
            )

            comparison_reply = (
                await run_in_threadpool(
                    compare_assessments,
                    recommendations,
                )
            )

            return ChatResponse(
                reply=comparison_reply,
                recommendations=recommendations,
                end_of_conversation=False,
            )

        # =================================================
        # LLM RESPONSE
        # =================================================

        logger.info(
            "Generating LLM response"
        )

        try:

            reply = await run_in_threadpool(
                generate_llm_response,
                latest_user_message,
                recommendations,
                context,
                intent,
            )

        except Exception as error:

            logger.exception(
                "LLM generation failed: %s",
                error,
            )

            top_names = [
                item.get("name", "")
                for item in recommendations[:3]
                if item.get("name")
            ]

            reply = (
                f"I found relevant SHL assessments including: "
                f"{', '.join(top_names)}."
            )

        # =================================================
        # END DETECTION
        # =================================================

        end_of_conversation = (
            detect_conversation_end(
                request.messages,
                recommendations,
            )
        )

        logger.info(
            "CHAT REQUEST COMPLETED SUCCESSFULLY"
        )

        return ChatResponse(
            reply=reply,
            recommendations=recommendations,
            end_of_conversation=end_of_conversation,
        )

    except Exception as error:

        logger.error(
            "CHAT ENDPOINT CRASHED"
        )

        logger.error(
            traceback.format_exc()
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )