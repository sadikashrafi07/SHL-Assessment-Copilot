# =========================================================
# app/config/settings.py
# FINAL ENTERPRISE SETTINGS v13
# FULLY FIXED + HIGH PRECISION + HIGH RECALL
# SHL ASSIGNMENT OPTIMIZED
# PRODUCTION READY
# =========================================================

from __future__ import annotations

from pathlib import Path

# =========================================================
# APPLICATION
# =========================================================

API_TITLE = "SHL Conversational Assessment Recommender"

API_VERSION = "13.0.0"

DEBUG = False

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"

CATALOG_FILE = DATA_DIR / "cleaned_catalog.json"

EMBEDDINGS_FILE = DATA_DIR / "catalog_embeddings.npy"

# =========================================================
# CONVERSATION
# =========================================================

MAX_CONVERSATION_TURNS = 8

MAX_CLARIFICATION_QUESTIONS = 2

MAX_CHAT_HISTORY_MESSAGES = 20

# =========================================================
# RESPONSE
# =========================================================

MAX_RECOMMENDATIONS = 10

FINAL_RECOMMENDATIONS = 10

FINAL_TOP_K = 10

# =========================================================
# RETRIEVAL
# =========================================================

TOP_K_SEMANTIC = 60

TOP_K_BM25 = 60

TOP_K_HYBRID = 40

TOP_K_RERANK = 20

# =========================================================
# THRESHOLDS
# =========================================================

MIN_SIMILARITY_THRESHOLD = 0.16

MIN_ACCEPTABLE_SCORE = 0.22

HIGH_CONFIDENCE_THRESHOLD = 0.78

HIGH_CONFIDENCE_SCORE = 0.82

LOW_CONFIDENCE_THRESHOLD = 0.40

# =========================================================
# EMBEDDINGS
# =========================================================

EMBEDDING_DIMENSION = 384

EMBEDDING_NORMALIZE = True

# =========================================================
# RUNTIME
# =========================================================

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

ENABLE_DYNAMIC_EXPLANATIONS = True

ENABLE_HARD_ROLE_FILTERING = True

ENABLE_ROLE_PENALIZATION = True

ENABLE_SKILL_OVERLAP_SCORING = True

ENABLE_QUERY_EXPANSION = True

ENABLE_RESULT_DIVERSITY = True

ENABLE_FUZZY_MATCHING = True

ENABLE_RESPONSE_CACHE = True

# =========================================================
# HYBRID WEIGHTS
# =========================================================

SEMANTIC_WEIGHT = 0.42

BM25_WEIGHT = 0.24

ROLE_WEIGHT = 0.22

SKILL_WEIGHT = 0.22

COMPETENCY_WEIGHT = 0.16

SENIORITY_WEIGHT = 0.08

DOMAIN_WEIGHT = 0.14

KEYWORD_WEIGHT = 0.22

TYPE_WEIGHT = 0.10

PHRASE_WEIGHT = 0.14

CONTEXT_WEIGHT = 0.10

LEXICAL_WEIGHT = 0.24

# =========================================================
# HARD BOOSTS
# =========================================================

ROLE_MATCH_BOOST = 0.14

ROLE_STRICT_MATCH_BOOST = 0.28

SKILL_STRICT_MATCH_BOOST = 0.24

COMPETENCY_MATCH_BOOST = 0.18

TECH_STACK_MATCH_BOOST = 0.16

LEADERSHIP_MATCH_BOOST = 0.12

COMMUNICATION_MATCH_BOOST = 0.10

COGNITIVE_MATCH_BOOST = 0.10

PERSONALITY_MATCH_BOOST = 0.08

SENIORITY_MATCH_BOOST = 0.08

DOMAIN_MATCH_BOOST = 0.08

EXACT_PHRASE_BOOST = 0.14

# =========================================================
# PENALTIES
# =========================================================

IRRELEVANT_TECH_PENALTY = 0.22

ROLE_MISMATCH_PENALTY = 0.26

DOMAIN_MISMATCH_PENALTY = 0.18

IRRELEVANT_LEADERSHIP_PENALTY = 0.12

IRRELEVANT_PERSONALITY_PENALTY = 0.10

# =========================================================
# RESULT DIVERSITY
# =========================================================

MAX_SAME_TYPE_RESULTS = 3

TYPE_LIMITS = {
    "K": 4,
    "P": 2,
    "A": 3,
    "S": 2,
    "L": 2,
}

# =========================================================
# QUERY EXPANSION
# =========================================================

ENABLE_ROLE_EXPANSION = True

ENABLE_COMPETENCY_EXPANSION = True

MAX_EXPANSION_TERMS = 80

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
        "organizational leadership",
    ],

    "communication": [
        "presentation skills",
        "stakeholder communication",
        "cross functional collaboration",
        "verbal communication",
        "client communication",
    ],

    "cognitive": [
        "logical reasoning",
        "critical thinking",
        "analytical thinking",
        "problem solving",
        "deductive reasoning",
    ],

    "personality": [
        "behavioral traits",
        "occupational personality",
        "motivation",
        "adaptability",
        "opq",
        "culture fit",
    ],

    "software engineer": [
        "coding",
        "algorithms",
        "problem solving",
        "technical assessment",
        "software development",
        "backend",
        "frontend",
    ],

    "backend developer": [
        "backend",
        "microservices",
        "api",
        "distributed systems",
        "fastapi",
        "django",
        "flask",
        "spring",
        "sql",
    ],

    "frontend developer": [
        "frontend",
        "react",
        "angular",
        "typescript",
        "ui",
        "javascript",
        "web development",
    ],

    "full stack developer": [
        "frontend",
        "backend",
        "react",
        "api",
        "microservices",
        "sql",
    ],

    "data scientist": [
        "machine learning",
        "statistics",
        "python",
        "analytics",
        "data analysis",
        "ai",
        "deep learning",
        "llm",
    ],

    "devops engineer": [
        "cloud",
        "aws",
        "docker",
        "kubernetes",
        "linux",
        "automation",
        "terraform",
        "ci/cd",
    ],

    "product manager": [
        "stakeholder management",
        "roadmapping",
        "strategy",
        "leadership",
        "communication",
        "cross functional",
    ],

    "python": [
        "django",
        "flask",
        "fastapi",
        "backend",
        "automation",
        "data science",
    ],

    "java": [
        "spring",
        "spring boot",
        "backend",
        "microservices",
    ],

    "javascript": [
        "react",
        "frontend",
        "nodejs",
        "web development",
    ],

    "cloud": [
        "aws",
        "azure",
        "gcp",
        "devops",
        "infrastructure",
    ],
}

# =========================================================
# ROLE COMPETENCIES
# =========================================================

ROLE_COMPETENCIES = {

    "software engineer": [
        "coding",
        "algorithms",
        "technical",
        "problem solving",
    ],

    "backend developer": [
        "backend",
        "api",
        "microservices",
        "distributed systems",
    ],

    "frontend developer": [
        "frontend",
        "react",
        "ui",
        "typescript",
    ],

    "full stack developer": [
        "frontend",
        "backend",
        "api",
        "react",
    ],

    "data scientist": [
        "machine learning",
        "statistics",
        "python",
        "analytics",
    ],

    "product manager": [
        "leadership",
        "stakeholder management",
        "strategy",
        "communication",
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
# ROLE PRIORITY MAP
# =========================================================

ROLE_PRIORITIES = {

    "product manager": {
        "preferred_types": {"L", "P", "S"},
        "avoid_keywords": {
            "java",
            ".net",
            "docker",
            "kubernetes",
        },
    },

    "backend developer": {
        "preferred_types": {"K", "A"},
        "avoid_keywords": {
            "sales",
            "marketing",
        },
    },

    "frontend developer": {
        "preferred_types": {"K", "A"},
        "avoid_keywords": {
            "sales",
            "marketing",
            "sap",
            "abap",
        },
    },

    "devops engineer": {
        "preferred_types": {"K", "A"},
        "avoid_keywords": {
            "personality",
            "behavioral",
        },
    },

    "data scientist": {
        "preferred_types": {"K", "A"},
        "avoid_keywords": {
            "sales",
            "marketing",
        },
    },
}

# =========================================================
# TEST TYPES
# =========================================================

TEST_TYPE_MAP = {
    "knowledge": "K",
    "technical": "K",
    "personality": "P",
    "cognitive": "A",
    "aptitude": "A",
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
# LLM
# =========================================================

LLM_MODEL = "llama-3.3-70b-versatile"

LLM_TEMPERATURE = 0.05

MAX_LLM_TOKENS = 512

# =========================================================
# RESPONSE GENERATION
# =========================================================

ALLOW_COMPARISON_RESPONSES = True

ALLOW_REFINEMENT = True

STRICT_CATALOG_GROUNDING = True

MIN_EXPLANATION_LENGTH = 60

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
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://shl-assessment-copilot.angadimohammadsadiq.workers.dev",
]

# =========================================================
# SECURITY
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

CACHE_SIZE = 256

ENABLE_PARALLEL_RETRIEVAL = False

PRELOAD_CATALOG = True

PRELOAD_EMBEDDINGS = True

USE_LAZY_LOADING = False

# =========================================================
# MEMORY OPTIMIZATION
# =========================================================

NUMPY_DTYPE = "float32"

ENABLE_BATCH_PROCESSING = True

BATCH_SIZE = 64

# =========================================================
# LOGGING
# =========================================================

LOG_LEVEL = "INFO"