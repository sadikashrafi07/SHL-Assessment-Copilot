# =========================================================
# app/config/settings.py
# =========================================================

from pathlib import Path

# =========================================================
# APPLICATION
# =========================================================

API_TITLE = "SHL Conversational Assessment Recommender"

API_VERSION = "6.1.0"

DEBUG = False

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"

CATALOG_FILE = DATA_DIR / "cleaned_catalog.json"

CHROMA_DB_PATH = str(DATA_DIR / "chroma_db")

# =========================================================
# API / CONVERSATION LIMITS
# =========================================================

MAX_CONVERSATION_TURNS = 10

MAX_CLARIFICATION_QUESTIONS = 2

MAX_CHAT_HISTORY_MESSAGES = 20

MAX_RECOMMENDATIONS = 10

FINAL_RECOMMENDATIONS = 6

# =========================================================
# RETRIEVAL PIPELINE
# =========================================================

TOP_K_RETRIEVAL = 30

TOP_K_BM25 = 30

TOP_K_SEMANTIC = 30

TOP_K_HYBRID = 25

TOP_K_RERANK = 15

FINAL_TOP_K = 10

# =========================================================
# THRESHOLDS
# =========================================================

MIN_SIMILARITY_THRESHOLD = 0.30

MIN_ACCEPTABLE_SCORE = 0.40

HIGH_CONFIDENCE_THRESHOLD = 0.75

HIGH_CONFIDENCE_SCORE = 0.72

# =========================================================
# EMBEDDINGS
# =========================================================

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

EMBEDDING_NORMALIZE = True

EMBEDDING_BATCH_SIZE = 32

# =========================================================
# CROSS ENCODER
# =========================================================

ENABLE_CROSS_ENCODER = True

CROSS_ENCODER_MODEL = (
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# =========================================================
# HYBRID RETRIEVAL
# =========================================================

ENABLE_HYBRID_RETRIEVAL = True

ENABLE_BM25 = True

ENABLE_SEMANTIC_SEARCH = True

ENABLE_METADATA_BOOSTING = True

# =========================================================
# MAIN RERANKER WEIGHTS
# REQUIRED BY reranker.py
# =========================================================

SEMANTIC_WEIGHT = 0.45

KEYWORD_WEIGHT = 0.25

ROLE_WEIGHT = 0.20

SOFT_SKILL_WEIGHT = 0.10

# =========================================================
# ADVANCED HYBRID WEIGHTS
# =========================================================

BM25_WEIGHT = 0.30

CROSS_ENCODER_WEIGHT = 0.25

# =========================================================
# ONTOLOGY BOOSTS
# =========================================================

ROLE_MATCH_BOOST = 0.20

COMPETENCY_MATCH_BOOST = 0.15

LEADERSHIP_MATCH_BOOST = 0.12

COMMUNICATION_MATCH_BOOST = 0.10

TECHNICAL_MATCH_BOOST = 0.12

PERSONALITY_MATCH_BOOST = 0.10

COGNITIVE_MATCH_BOOST = 0.10

SENIORITY_MATCH_BOOST = 0.08

DOMAIN_MATCH_BOOST = 0.07

# =========================================================
# LEGACY HEURISTIC BOOSTS
# =========================================================

EXACT_ROLE_BOOST = 20

LEADERSHIP_BOOST = 15

COMMUNICATION_BOOST = 12

PERSONALITY_BOOST = 14

COGNITIVE_BOOST = 12

TECHNICAL_BOOST = 14

MANAGERIAL_BOOST = 15

STAKEHOLDER_BOOST = 10

# =========================================================
# TEST TYPES
# MUST MATCH:
# - preprocess.py
# - schemas.py
# - retrieval.py
# - reranker.py
# =========================================================

TEST_TYPE_MAP = {
    "knowledge": "K",
    "personality": "P",
    "cognitive": "C",
    "situational": "S",
    "leadership": "L",
}

VALID_TEST_TYPES = {
    "K",
    "P",
    "C",
    "S",
    "L",
}

# =========================================================
# DIVERSITY CONTROL
# =========================================================

ENABLE_RESULT_DIVERSITY = True

MAX_SAME_TYPE_RESULTS = 3

TYPE_LIMITS = {
    "K": 4,
    "P": 3,
    "C": 3,
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

MAX_EXPANSION_TERMS = 20

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
        "cross functional collaboration",
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
        "reasoning",
        "problem solving",
    ],

    "devops engineer": [
        "cloud",
        "aws",
        "kubernetes",
        "docker",
        "infrastructure",
        "automation",
        "linux",
        "monitoring",
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
        "decision making",
    ],

    "software engineer": [
        "coding",
        "technical",
        "problem solving",
        "analytical",
    ],

    "java developer": [
        "java",
        "backend",
        "problem solving",
    ],

    "data analyst": [
        "analytics",
        "numerical reasoning",
        "critical thinking",
    ],

    "data scientist": [
        "machine learning",
        "statistics",
        "python",
        "analytics",
        "reasoning",
        "problem solving",
    ],

    "devops engineer": [
        "cloud",
        "aws",
        "docker",
        "kubernetes",
        "automation",
        "linux",
        "infrastructure",
    ],

    "sales manager": [
        "communication",
        "relationship building",
        "leadership",
    ],

    "hr manager": [
        "behavioral assessment",
        "leadership",
        "collaboration",
    ],
}

# =========================================================
# CHROMA
# =========================================================

CHROMA_COLLECTION_NAME = "shl_assessments"

ANONYMIZED_TELEMETRY = False

# =========================================================
# LLM
# =========================================================

LLM_MODEL = "llama-3.3-70b-versatile"

LLM_TEMPERATURE = 0.1

MAX_LLM_TOKENS = 350

# =========================================================
# RESPONSE GENERATION
# =========================================================

ALLOW_COMPARISON_RESPONSES = True

ALLOW_REFINEMENT = True

STRICT_CATALOG_GROUNDING = True

MIN_EXPLANATION_LENGTH = 30

MAX_EXPLANATION_LENGTH = 300

# =========================================================
# CLARIFICATION RULES
# =========================================================

MANDATORY_FIELDS = [
    "role",
]

OPTIONAL_FIELDS = [
    "seniority",
    "assessment_focus",
    "soft_skills",
]

VAGUE_QUERIES = [
    "need assessment",
    "recommend assessment",
    "hiring",
    "test for candidate",
]

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
# GUARDRAILS
# =========================================================

OFFTOPIC_KEYWORDS = [
    "salary",
    "politics",
    "religion",
    "investment",
    "crypto",
    "medical advice",
    "lawsuit",
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

ENABLE_PARALLEL_RETRIEVAL = True

# =========================================================
# LOGGING
# =========================================================

LOG_LEVEL = "INFO"