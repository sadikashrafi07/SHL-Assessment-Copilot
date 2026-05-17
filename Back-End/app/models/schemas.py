from enum import Enum
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
)

# =========================================================
# MESSAGE ROLES
# =========================================================

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


# =========================================================
# TEST TYPES
# =========================================================

class TestType(str, Enum):
    K = "K"  # Knowledge
    P = "P"  # Personality
    A = "A"  # Cognitive Ability
    S = "S"  # Situational Judgment
    L = "L"  # Leadership


# =========================================================
# RECOMMENDATION STRENGTH
# =========================================================

class RecommendationStrength(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# =========================================================
# INPUT MESSAGE
# =========================================================

class Message(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    role: Role

    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )


# =========================================================
# CHAT REQUEST
# =========================================================

class ChatRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    messages: List[Message] = Field(
        ...,
        min_length=1,
        max_length=20,
    )


# =========================================================
# RECOMMENDATION
# =========================================================

class Recommendation(BaseModel):

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # =====================================================
    # REQUIRED CORE FIELDS
    # =====================================================

    name: str = Field(
        ...,
        min_length=2,
        max_length=300,
    )

    url: HttpUrl

    test_type: TestType

    # =====================================================
    # FRONTEND FRIENDLY OPTIONAL FIELDS
    # =====================================================

    description: Optional[str] = Field(
        default=None,
        max_length=2500,
    )

    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    recommendation_strength: Optional[
        RecommendationStrength
    ] = None

    explanation: Optional[str] = Field(
        default=None,
        max_length=2500,
    )


# =========================================================
# FINAL PRODUCTION RESPONSE
# =========================================================

class ChatResponse(BaseModel):

    """
    Production-safe schema.

    Compatible with:
    - SHL evaluator
    - Frontend UI
    - Recommendation cards
    - Comparison views
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    reply: str = Field(
        ...,
        min_length=1,
        max_length=6000,
    )

    recommendations: List[
        Recommendation
    ] = Field(
        default_factory=list,
        max_length=10,
    )

    end_of_conversation: bool = False