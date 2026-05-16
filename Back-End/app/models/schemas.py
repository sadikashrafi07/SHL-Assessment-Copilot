# =========================================================
# app/models/schemas.py
# =========================================================

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# =========================================================
# MESSAGE ROLES
# =========================================================

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


# =========================================================
# TEST TYPES
# MUST MATCH:
# - preprocess.py
# - retrieval.py
# - reranker.py
# - settings.py
# =========================================================

class TestType(str, Enum):

    # Knowledge / Technical
    K = "K"

    # Personality
    P = "P"

    # Cognitive Ability
    A = "A"

    # Situational Judgement
    S = "S"

    # Behavioral
    B = "B"


# =========================================================
# INPUT MESSAGE
# =========================================================

class Message(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    role: Role

    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Conversation message content",
    )


# =========================================================
# CHAT REQUEST
# =========================================================

class ChatRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
    )

    messages: List[Message] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Conversation history",
    )


# =========================================================
# RECOMMENDATION
# =========================================================

class Recommendation(BaseModel):

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=300,
        description="Assessment name",
    )

    url: HttpUrl

    test_type: TestType

    description: Optional[str] = Field(
        default=None,
        max_length=2000,
    )

    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Final ranking score",
    )

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence level",
    )

    recommendation_strength: Optional[
        str
    ] = Field(
        default=None,
        max_length=100,
    )

    explanation: Optional[str] = Field(
        default=None,
        max_length=2000,
    )


# =========================================================
# OUTPUT RESPONSE
# =========================================================

class ChatResponse(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
    )

    reply: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Assistant response",
    )

    recommendations: List[
        Recommendation
    ] = Field(
        default_factory=list,
    )

    end_of_conversation: bool = Field(
        default=False,
    )