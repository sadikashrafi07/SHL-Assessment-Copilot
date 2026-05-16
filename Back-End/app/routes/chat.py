# =========================================================
# app/routes/chat.py
# =========================================================

from __future__ import annotations

import logging

from fastapi import APIRouter

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
def health() -> dict:
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
def chat(
    request: ChatRequest,
) -> ChatResponse:

    try:

        # =================================================
        # VALIDATE REQUEST
        # =================================================

        if not request.messages:
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
            "User message: %s",
            latest_user_message,
        )

        if not latest_user_message:
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
                "Unsafe query blocked."
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
        # FIXED: REMOVED context=context
        # =================================================

        raw_results = (
            search_assessments(
                query=search_query
            )
            or []
        )

        logger.info(
            "Retrieved %s candidates",
            len(raw_results),
        )

        if not raw_results:
            return ChatResponse(
                reply=(
                    "I could not find sufficiently "
                    "relevant SHL assessments.\n\n"
                    "Try specifying:\n"
                    "- exact role\n"
                    "- seniority\n"
                    "- technical stack\n"
                    "- leadership requirements\n"
                    "- communication needs\n"
                    "- cognitive or personality focus"
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =================================================
        # RECOMMENDATION PIPELINE
        # =================================================

        recommendations = (
            generate_recommendations(
                results=raw_results,
                query=search_query,
                context=context,
            )
            or []
        )

        logger.info(
            "Final recommendations: %s",
            len(recommendations),
        )

        if not recommendations:
            return ChatResponse(
                reply=(
                    "I found possible matches, "
                    "but none passed final "
                    "quality validation."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        # =================================================
        # COMPARISON MODE
        # =================================================

        if intent == "comparison":

            comparison_reply = (
                compare_assessments(
                    recommendations
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

        try:

            reply = (
                generate_llm_response(
                    user_query=latest_user_message,
                    recommendations=recommendations,
                    context=context,
                    intent=intent,
                )
            )

        except Exception as error:

            logger.exception(
                "LLM response failed: %s",
                error,
            )

            top_names = [
                item.get(
                    "name",
                    ""
                )
                for item in recommendations[:3]
                if item.get("name")
            ]

            if top_names:
                reply = (
                    "I found relevant SHL "
                    "assessments including: "
                    f"{', '.join(top_names)}."
                )
            else:
                reply = (
                    "I found relevant SHL "
                    "assessments for your query."
                )

        # =================================================
        # END CONVERSATION DETECTION
        # =================================================

        end_of_conversation = (
            detect_conversation_end(
                request.messages,
                recommendations,
            )
        )

        # =================================================
        # FINAL RESPONSE
        # =================================================

        logger.info(
            "Chat response generated successfully."
        )

        return ChatResponse(
            reply=reply,
            recommendations=recommendations,
            end_of_conversation=end_of_conversation,
        )

    except Exception as error:

        logger.exception(
            "Chat endpoint failed: %s",
            error,
        )

        return ChatResponse(
            reply=(
                "An internal error occurred "
                "while processing the request."
            ),
            recommendations=[],
            end_of_conversation=False,
        )