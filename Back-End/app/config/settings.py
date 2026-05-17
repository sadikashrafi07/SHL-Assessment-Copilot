# =========================================================
# app/config/settings.py
# PRODUCTION-OPTIMIZED SETTINGS
# Railway + Hybrid Retrieval + Low Memory
# =========================================================

from pathlib import Path

# =========================================================
# APPLICATION
# =========================================================

API_TITLE = "SHL Conversational Assessment Recommender"

API_VERSION = "9.0.0"

DEBUG = False

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"

CATALOG_FILE = DATA_DIR / "cleaned_catalog.json"

# PRECOMPUTED EMBEDDINGS
# Generated offline using build_embeddings.py
EMBEDDINGS_FILE = DATA_DIR / "catalog_embeddings.npy"

# =========================================================
# CONVERSATION
# =========================================================

# SHL evaluator conversation limit
MAX_CONVERSATION_TURNS = 8

MAX_CLARIFICATION_QUESTIONS = 2

MAX_CHAT_HISTORY_MESSAGES = 20

# =========================================================
# FINAL RESPONSE
# =========================================================

MAX_RECOMMENDATIONS = 10

# Better Recall@10
FINAL_RECOMMENDATIONS = 8

FINAL_TOP_K = 8

# =========================================================
# RETRIEVAL PIPELINE
# =========================================================

TOP_K_SEMANTIC = 20

TOP_K_BM25 = 20

TOP_K_HYBRID = 15

TOP_K_RERANK = 10

# =========================================================
# THRESHOLDS
# =========================================================

# Lower threshold improves recall
MIN_SIMILARITY_THRESHOLD = 0.30

MIN_ACCEPTABLE_SCORE = 0.35

HIGH_CONFIDENCE_THRESHOLD = 0.78

HIGH_CONFIDENCE_SCORE = 0.80

# =========================================================
# EMBEDDINGS
# =========================================================

# EMBEDDINGS ARE PRECOMPUTED OFFLINE
# DO NOT LOAD sentence-transformers at runtime

EMBEDDING_DIMENSION = 384

EMBEDDING_NORMALIZE = True

# =========================================================
# RUNTIME OPTIMIZATION
# =========================================================

# Critical Railway optimization
LOAD_EMBEDDINGS_IN_MEMORY = True

USE_NUMPY_COSINE_SIMILARITY = True

USE_FAISS = False

USE_SENTENCE_TRANSFORMERS_RUNTIME = False

USE_CROSS_ENCODER_RUNTIME = False

# =========================================================
# HYBRID RETRIEVAL
# =========================================================

ENABLE_HYBRID_RETRIEVAL = True

ENABLE_BM25 = True

ENABLE_SEMANTIC_SEARCH = True

ENABLE_METADATA_BOOSTING = True

ENABLE_RERANKING = True

# =========================================================
# HYBRID WEIGHTS
# =========================================================

# Tuned for lightweight embeddings
SEMANTIC_WEIGHT = 0.45

BM25_WEIGHT = 0.35

ROLE_WEIGHT = 0.10

COMPETENCY_WEIGHT = 0.05

SENIORITY_WEIGHT = 0.03

DOMAIN_WEIGHT = 0.02

# =========================================================
# METADATA BOOSTS
# =========================================================

ROLE_MATCH_BOOST = 0.15

COMPETENCY_MATCH_BOOST = 0.10

TECH_STACK_MATCH_BOOST = 0.10

LEADERSHIP_MATCH_BOOST = 0.08

COMMUNICATION_MATCH_BOOST = 0.06

COGNITIVE_MATCH_BOOST = 0.06

PERSONALITY_MATCH_BOOST = 0.06

SENIORITY_MATCH_BOOST = 0.05

DOMAIN_MATCH_BOOST = 0.05

# =========================================================
# TEST TYPES
# =========================================================

TEST_TYPE_MAP = {
    "knowledge": "K",
    "personality": "P",
    "cognitive": "A",
    "situational": "S",
    "leadership": "L",
}

VALID_TEST_TYPES = {
    "K",
    "P",
    "A",
    "S",
    "L",
}

# =========================================================
# RESULT DIVERSITY
# =========================================================

ENABLE_RESULT_DIVERSITY = True

MAX_SAME_TYPE_RESULTS = 4

TYPE_LIMITS = {
    "K": 4,
    "P": 3,
    "A": 3,
    "S": 2,
    "L": 3,
}

# =========================================================
# QUERY EXPANSION
# =========================================================

ENABLE_QUERY_EXPANSION = True

ENABLE_ROLE_EXPANSION = True

ENABLE_COMPETENCY_EXPANSION = True

ENABLE_FUZZY_MATCHING = True

MAX_EXPANSION_TERMS = 25

# =========================================================
# QUERY EXPANSIONS
# =========================================================

QUERY_EXPANSIONS = {

    "leadership": [
        "people management",
        "team leadership",
        "executive presence",
        "decision making",
        "strategic thinking",
    ],

    "communication": [
        "presentation skills",
        "stakeholder communication",
        "cross functional collaboration",
        "verbal communication",
    ],

    "cognitive": [
        "logical reasoning",
        "critical thinking",
        "analytical thinking",
        "problem solving",
    ],

    "personality": [
        "behavioral traits",
        "occupational personality",
        "motivation",
        "adaptability",
        "opq",
    ],

    "product manager": [
        "stakeholder management",
        "roadmapping",
        "strategy",
        "leadership",
    ],

    "software engineer": [
        "coding",
        "algorithms",
        "problem solving",
        "technical assessment",
    ],

    "data scientist": [
        "machine learning",
        "statistics",
        "python",
        "analytics",
        "data analysis",
    ],

    "devops engineer": [
        "cloud",
        "aws",
        "kubernetes",
        "docker",
        "linux",
        "automation",
    ],
}

# =========================================================
# ROLE COMPETENCIES
# =========================================================

ROLE_COMPETENCIES = {

    "product manager": [
        "leadership",
        "stakeholder management",
        "strategy",
        "communication",
    ],

    "software engineer": [
        "coding",
        "technical",
        "problem solving",
    ],

    "java developer": [
        "java",
        "backend",
        "algorithms",
    ],

    "data scientist": [
        "machine learning",
        "statistics",
        "python",
        "analytics",
    ],

    "devops engineer": [
        "cloud",
        "aws",
        "docker",
        "kubernetes",
        "linux",
    ],
}

# =========================================================
# LLM
# =========================================================

LLM_MODEL = "llama-3.3-70b-versatile"

LLM_TEMPERATURE = 0.1

MAX_LLM_TOKENS = 512

# =========================================================
# RESPONSE GENERATION
# =========================================================

ALLOW_COMPARISON_RESPONSES = True

ALLOW_REFINEMENT = True

STRICT_CATALOG_GROUNDING = True

MIN_EXPLANATION_LENGTH = 40

MAX_EXPLANATION_LENGTH = 300

# =========================================================
# VALIDATION
# =========================================================

STRICT_URL_VALIDATION = True

REQUIRE_SHL_DOMAIN = True

REMOVE_DUPLICATES = True

MIN_NAME_LENGTH = 3

MAX_NAME_LENGTH = 200

ALLOWED_DOMAINS = [
    "https://www.shl.com",
]

# =========================================================
# DEPLOYMENT
# =========================================================

EVALUATION_MODE = False

RAILWAY_DEPLOYMENT = True

LOW_MEMORY_MODE = True

# =========================================================
# CORS
# =========================================================

ALLOWED_ORIGINS = [

    # Local development
    "http://localhost:8080",
    "http://127.0.0.1:8080",

    # Cloudflare frontend
    "https://shl-assessment-copilot.angadimohammadsadiq.workers.dev",
]

# =========================================================
# GUARDRAILS
# =========================================================

OFFTOPIC_KEYWORDS = [
    "salary",
    "politics",
    "religion",
    "investment",
    "crypto",
    "medical advice",
]

BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "reveal system prompt",
    "show hidden prompt",
    "developer message",
    "jailbreak",
]

# =========================================================
# PERFORMANCE
# =========================================================

ENABLE_RESPONSE_CACHE = True

CACHE_SIZE = 256

# Railway RAM optimization
ENABLE_PARALLEL_RETRIEVAL = False

PRELOAD_CATALOG = True

PRELOAD_EMBEDDINGS = True

USE_LAZY_LOADING = False

# =========================================================
# LOGGING
# =========================================================

LOG_LEVEL = "INFO"