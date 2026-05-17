# =========================================================
# scripts/preprocess.py
# Production-Grade SHL Catalog Enrichment Pipeline
# Optimized for:
# - Hybrid Retrieval
# - BM25
# - Semantic Search
# - Railway Deployment
# - BGE Embeddings
# =========================================================

from __future__ import annotations

import json
import re

from collections import Counter
from collections import defaultdict

from pathlib import Path

from typing import Any

# =========================================================
# FILES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "shl_product_catalog.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "cleaned_catalog.json"
)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input catalog not found: {INPUT_FILE}"
    )

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

# =========================================================
# TEST TYPE MAP
# =========================================================

TEST_TYPE_MAP = {
    "knowledge": "K",
    "personality": "P",
    "cognitive": "A",
    "situational": "S",
    "leadership": "L",
}

# =========================================================
# SEMANTIC SYNONYMS
# =========================================================

SEMANTIC_SYNONYMS = {

    # SOFTWARE
    "software engineer":
        "software developer",

    "backend engineer":
        "backend developer",

    "frontend engineer":
        "frontend developer",

    "full stack engineer":
        "full stack developer",

    "developer engineer":
        "software developer",

    "programmer":
        "software developer",

    # AI
    "artificial intelligence":
        "ai",

    "machine learning":
        "ai",

    # SHL
    "occupational personality questionnaire":
        "opq",

    "situational judgment":
        "situational judgement",

    # MANAGEMENT
    "people management":
        "leadership",

    "stakeholder engagement":
        "stakeholder management",

    "cross functional":
        "cross-functional",

    "project lead":
        "project manager",

    "product owner":
        "product manager",

    "business analyst":
        "analyst",
}

# =========================================================
# COMPETENCY GRAPH
# =========================================================

COMPETENCY_GRAPH = {

    "stakeholder management": [
        "communication",
        "leadership",
        "collaboration",
        "relationship management",
        "influence",
        "cross-functional collaboration",
    ],

    "leadership": [
        "people management",
        "decision making",
        "strategic thinking",
        "coaching",
        "influence",
        "team management",
    ],

    "communication": [
        "presentation",
        "verbal communication",
        "written communication",
        "collaboration",
        "teamwork",
    ],

    "problem solving": [
        "analytical thinking",
        "critical thinking",
        "reasoning",
        "decision making",
    ],

    "software development": [
        "coding",
        "programming",
        "debugging",
        "algorithms",
        "system design",
    ],

    "devops": [
        "cloud",
        "aws",
        "docker",
        "kubernetes",
        "linux",
        "automation",
    ],

    "data science": [
        "statistics",
        "python",
        "analytics",
        "machine learning",
        "data analysis",
    ],
}

# =========================================================
# ROLE ONTOLOGY
# =========================================================

ROLE_ONTOLOGY = {

    "software developer": {
        "skills": [
            "java",
            "python",
            "sql",
            "coding",
            "programming",
            "algorithms",
            "debugging",
            "software development",
        ],
        "threshold": 2,
    },

    "backend developer": {
        "skills": [
            "api",
            "backend",
            "microservices",
            "sql",
            "python",
            "java",
        ],
        "threshold": 2,
    },

    "frontend developer": {
        "skills": [
            "frontend",
            "react",
            "javascript",
            "typescript",
            "ui",
        ],
        "threshold": 2,
    },

    "full stack developer": {
        "skills": [
            "frontend",
            "backend",
            "react",
            "api",
            "sql",
        ],
        "threshold": 2,
    },

    "product manager": {
        "skills": [
            "stakeholder management",
            "roadmapping",
            "strategy",
            "leadership",
            "communication",
        ],
        "threshold": 2,
    },

    "engineering manager": {
        "skills": [
            "leadership",
            "people management",
            "strategic thinking",
            "decision making",
        ],
        "threshold": 2,
    },

    "data scientist": {
        "skills": [
            "python",
            "statistics",
            "analytics",
            "machine learning",
            "data analysis",
        ],
        "threshold": 2,
    },

    "devops engineer": {
        "skills": [
            "aws",
            "docker",
            "kubernetes",
            "linux",
            "cloud",
        ],
        "threshold": 2,
    },

    "sales professional": {
        "skills": [
            "communication",
            "persuasion",
            "relationship management",
        ],
        "threshold": 2,
    },
}

# =========================================================
# DOMAIN VOCABULARY
# =========================================================

DOMAIN_MAP = {

    "technical": {

        "java",
        "python",
        "sql",

        "react",
        "node",
        "javascript",
        "typescript",

        "backend",
        "frontend",
        "full stack",

        "api",
        "microservices",

        "cloud",
        "aws",
        "docker",
        "kubernetes",

        "linux",
        "devops",

        "software",
        "engineering",
        "developer",

        "coding",
        "programming",
        "algorithms",
        "system design",
    },

    "cognitive": {
        "reasoning",
        "logical",
        "numerical",
        "verbal",
        "problem solving",
        "critical thinking",
        "analytical",
        "general ability",
        "deductive",
        "inductive",
    },

    "personality": {
        "personality",
        "behavioral",
        "adaptability",
        "motivation",
        "resilience",
        "culture fit",
        "opq",
    },

    "leadership": {
        "leadership",
        "management",
        "stakeholder management",
        "people management",
        "strategy",
        "executive",
        "decision making",
    },

    "communication": {
        "communication",
        "presentation",
        "written communication",
        "verbal communication",
        "collaboration",
        "teamwork",
    },

    "situational": {
        "situational judgement",
        "scenario",
        "judgement",
        "decision making",
    },
}

# =========================================================
# SENIORITY SIGNALS
# =========================================================

SENIORITY_SIGNALS = {

    "junior": {
        "entry level",
        "graduate",
        "foundational",
        "basic",
    },

    "mid": {
        "stakeholder",
        "collaboration",
        "project ownership",
    },

    "senior": {
        "leadership",
        "strategy",
        "management",
        "decision making",
    },

    "executive": {
        "executive",
        "organizational leadership",
        "enterprise",
    },
}

# =========================================================
# INTENT TAGS
# =========================================================

INTENT_KEYWORDS = {

    "technical_screening": {
        "coding",
        "java",
        "python",
        "developer",
        "technical",
    },

    "leadership_assessment": {
        "leadership",
        "management",
        "stakeholder",
        "executive",
    },

    "behavioral_assessment": {
        "personality",
        "behavioral",
        "adaptability",
        "motivation",
    },

    "cognitive_evaluation": {
        "reasoning",
        "critical thinking",
        "analytical",
        "problem solving",
    },

    "communication_assessment": {
        "communication",
        "presentation",
        "collaboration",
    },
}

# =========================================================
# HELPERS
# =========================================================

def slugify(text: str) -> str:

    return re.sub(
        r"[^a-z0-9]+",
        "-",
        text.lower(),
    ).strip("-")


def clean_text(text: Any) -> str:

    if text is None:
        return ""

    if isinstance(text, list):
        text = " ".join(
            str(x)
            for x in text
        )

    text = str(text).lower()

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-z0-9+#.\-/ ]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def normalize_text(text: Any) -> str:

    text = clean_text(text)

    for source, target in (
        SEMANTIC_SYNONYMS.items()
    ):

        text = re.sub(
            rf"\b{re.escape(source)}\b",
            target,
            text,
        )

    return text


def keyword_match(
    text: str,
    keyword: str,
) -> bool:

    return bool(
        re.search(
            rf"\b{re.escape(keyword)}\b",
            text,
        )
    )


def extract_matches(
    text: str,
    vocabulary: set[str],
) -> list[str]:

    matches = set()

    for term in vocabulary:

        if keyword_match(
            text,
            term,
        ):
            matches.add(term)

    return sorted(matches)


def infer_domains(
    text: str,
) -> list[str]:

    domains = []

    for domain, keywords in (
        DOMAIN_MAP.items()
    ):

        if any(
            keyword_match(text, kw)
            for kw in keywords
        ):
            domains.append(domain)

    return sorted(set(domains))


def infer_roles(
    text: str,
) -> list[str]:

    matched_roles = []

    for role, config in (
        ROLE_ONTOLOGY.items()
    ):

        score = 0

        for skill in config["skills"]:

            if keyword_match(
                text,
                skill,
            ):
                score += 1

        if score >= config["threshold"]:
            matched_roles.append(role)

    return sorted(set(matched_roles))


def expand_competencies(
    skills: list[str],
) -> list[str]:

    expanded = set(skills)

    for skill in skills:

        related = COMPETENCY_GRAPH.get(
            skill,
            [],
        )

        expanded.update(related)

    return sorted(expanded)


def infer_seniority(
    text: str,
) -> list[str]:

    levels = []

    for level, signals in (
        SENIORITY_SIGNALS.items()
    ):

        if any(
            keyword_match(text, signal)
            for signal in signals
        ):
            levels.append(level)

    return sorted(set(levels))


def infer_intents(
    text: str,
) -> list[str]:

    intents = []

    for intent, keywords in (
        INTENT_KEYWORDS.items()
    ):

        if any(
            keyword_match(text, kw)
            for kw in keywords
        ):
            intents.append(intent)

    return sorted(set(intents))


def infer_test_type(
    record: dict[str, Any],
) -> str:

    scores = {

        "knowledge":
            len(record["technical_skills"]) * 1.2,

        "cognitive":
            len(record["cognitive_traits"]) * 1.4,

        "personality":
            len(record["personality_traits"]) * 1.6,

        "situational":
            len(record["situational_traits"]) * 1.3,

        "leadership":
            len(record["leadership_traits"]) * 1.5,
    }

    if scores["leadership"] >= 2:
        return "L"

    if scores["personality"] >= 2:
        return "P"

    if scores["cognitive"] >= 2:
        return "A"

    best = max(
        scores,
        key=scores.get,
    )

    if scores[best] <= 0:
        return "K"

    return TEST_TYPE_MAP[best]


def normalize_weight(
    score: int,
    total: int,
) -> float:

    if total <= 0:
        return 0.0

    return round(
        score / total,
        3,
    )

# =========================================================
# LOAD RAW DATA
# =========================================================

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8",
) as file:

    raw_data = json.load(file)

# =========================================================
# PROCESSING
# =========================================================

processed = []

seen_urls = set()
seen_names = set()

for item in raw_data:

    try:

        raw_name = str(
            item.get("name", "")
        ).strip()

        raw_url = str(
            item.get(
                "link",
                item.get("url", ""),
            )
        ).strip()

        if not raw_name:
            continue

        if not raw_url:
            continue

        if not raw_url.startswith(
            "https://www.shl.com"
        ):
            continue

        normalized_name = normalize_text(
            raw_name
        )

        if normalized_name in seen_names:
            continue

        if raw_url in seen_urls:
            continue

        seen_names.add(normalized_name)
        seen_urls.add(raw_url)

        description = clean_text(
            item.get(
                "description",
                "",
            )
        )

        keys = item.get(
            "keys",
            [],
        )

        job_levels = item.get(
            "job_levels",
            [],
        )

        languages = item.get(
            "languages",
            [],
        )

        duration = clean_text(
            item.get(
                "duration",
                "",
            )
        )

        remote = clean_text(
            item.get(
                "remote",
                "",
            )
        )

        adaptive = clean_text(
            item.get(
                "adaptive",
                "",
            )
        )

        source_text = normalize_text(
            " ".join(
                [
                    raw_name,
                    description,
                    " ".join(keys),
                    " ".join(job_levels),
                    " ".join(languages),
                    duration,
                    remote,
                    adaptive,
                ]
            )
        )

        technical_skills = extract_matches(
            source_text,
            DOMAIN_MAP["technical"],
        )

        cognitive_traits = extract_matches(
            source_text,
            DOMAIN_MAP["cognitive"],
        )

        personality_traits = extract_matches(
            source_text,
            DOMAIN_MAP["personality"],
        )

        leadership_traits = extract_matches(
            source_text,
            DOMAIN_MAP["leadership"],
        )

        communication_skills = extract_matches(
            source_text,
            DOMAIN_MAP["communication"],
        )

        situational_traits = extract_matches(
            source_text,
            DOMAIN_MAP["situational"],
        )

        all_traits = sorted(
            set(
                technical_skills
                + cognitive_traits
                + personality_traits
                + leadership_traits
                + communication_skills
                + situational_traits
            )
        )

        expanded_competencies = (
            expand_competencies(
                all_traits
            )
        )

        inferred_domains = infer_domains(
            source_text
        )

        inferred_roles = infer_roles(
            source_text
        )

        inferred_seniority = (
            infer_seniority(
                source_text
            )
        )

        inferred_intents = (
            infer_intents(
                source_text
            )
        )

        negative_domains = []

        if "technical" in inferred_domains:
            negative_domains.extend([
                "sales",
                "executive",
            ])

        if "leadership" in inferred_domains:
            negative_domains.extend([
                "entry-level",
            ])

        negative_domains = sorted(
            set(negative_domains)
        )

        record = {

            "id":
                slugify(raw_name),

            "name":
                raw_name,

            "url":
                raw_url,

            "description":
                item.get(
                    "description",
                    "",
                ).strip(),

            "domains":
                inferred_domains,

            "roles":
                inferred_roles,

            "recommended_seniority":
                inferred_seniority,

            "intents":
                inferred_intents,

            "job_levels":
                job_levels,

            "languages":
                languages,

            "duration":
                duration,

            "remote":
                remote,

            "adaptive":
                adaptive,

            "technical_skills":
                technical_skills,

            "cognitive_traits":
                cognitive_traits,

            "personality_traits":
                personality_traits,

            "leadership_traits":
                leadership_traits,

            "communication_skills":
                communication_skills,

            "situational_traits":
                situational_traits,

            "expanded_competencies":
                expanded_competencies,

            "negative_domains":
                negative_domains,

            "comparison_metadata": {

                "domains":
                    inferred_domains,

                "roles":
                    inferred_roles,

                "duration":
                    duration,

                "adaptive":
                    adaptive,

                "remote":
                    remote,

                "job_levels":
                    job_levels,

                "languages":
                    languages,
            },
        }

        # =================================================
        # TEST TYPE
        # =================================================

        record["test_type"] = (
            infer_test_type(record)
        )

        # =================================================
        # WEIGHTS
        # =================================================

        total_traits = max(
            len(all_traits),
            1,
        )

        record["weights"] = {

            "technical":
                normalize_weight(
                    len(technical_skills),
                    total_traits,
                ),

            "cognitive":
                normalize_weight(
                    len(cognitive_traits),
                    total_traits,
                ),

            "personality":
                normalize_weight(
                    len(personality_traits),
                    total_traits,
                ),

            "leadership":
                normalize_weight(
                    len(leadership_traits),
                    total_traits,
                ),

            "communication":
                normalize_weight(
                    len(communication_skills),
                    total_traits,
                ),

            "situational":
                normalize_weight(
                    len(situational_traits),
                    total_traits,
                ),
        }

        # =================================================
        # STRUCTURED EMBEDDING TEXT
        # =================================================

        record["embedding_text"] = f"""
Assessment Name:
{raw_name}

Description:
{description}

Domains:
{' '.join(inferred_domains)}

Roles:
{' '.join(inferred_roles)}

Seniority:
{' '.join(inferred_seniority)}

Intent:
{' '.join(inferred_intents)}

Technical Skills:
{' '.join(technical_skills)}

Cognitive Traits:
{' '.join(cognitive_traits)}

Personality Traits:
{' '.join(personality_traits)}

Leadership Traits:
{' '.join(leadership_traits)}

Communication Skills:
{' '.join(communication_skills)}

Situational Traits:
{' '.join(situational_traits)}

Expanded Competencies:
{' '.join(expanded_competencies)}

Duration:
{duration}

Remote:
{remote}

Adaptive:
{adaptive}

Assessment Type:
{record['test_type']}
""".strip()

        processed.append(record)

    except Exception as error:

        print(
            f"Processing error: {error}"
        )

# =========================================================
# SORT
# =========================================================

processed.sort(
    key=lambda item:
    item["name"].lower()
)

# =========================================================
# SAVE
# =========================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        processed,
        file,
        indent=2,
        ensure_ascii=False,
    )

# =========================================================
# SUMMARY
# =========================================================

counter = Counter()

domain_counter = defaultdict(int)

for item in processed:

    counter[item["test_type"]] += 1

    for domain in item["domains"]:

        domain_counter[domain] += 1

print("=" * 80)

print(
    f"Processed Assessments : {len(processed)}"
)

print(
    f"Test Type Distribution: {dict(counter)}"
)

print(
    f"Domain Distribution   : {dict(domain_counter)}"
)

print(
    f"Output File           : {OUTPUT_FILE}"
)

print("=" * 80)