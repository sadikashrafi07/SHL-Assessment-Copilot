# =========================================================
# scripts/preprocess.py
# Production-Grade SHL Catalog Enrichment Pipeline
# =========================================================

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# =========================================================
# FILES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "shl_product_catalog.json"

OUTPUT_FILE = BASE_DIR / "data" / "cleaned_catalog.json"

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
    "software engineer": "software developer",
    "backend engineer": "software developer",
    "frontend engineer": "software developer",
    "full stack engineer": "software developer",
    "developer engineer": "software developer",
    "programmer": "software developer",
    "artificial intelligence": "ai",
    "machine learning": "ai",
    "occupational personality questionnaire": "opq",
    "situational judgment": "situational judgement",
    "people management": "leadership",
    "cross functional": "cross-functional",
    "stakeholder engagement": "stakeholder management",
    "product owner": "product manager",
    "project lead": "project manager",
    "business analyst": "analyst",
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

    "product management": [
        "roadmapping",
        "strategy",
        "stakeholder management",
        "prioritization",
        "leadership",
    ],

    "software development": [
        "coding",
        "programming",
        "debugging",
        "algorithms",
        "system design",
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
            "software development",
            "debugging",
            "algorithms",
        ],
        "domains": [
            "technical",
            "cognitive",
        ],
        "threshold": 2,
    },

    "product manager": {
        "skills": [
            "stakeholder management",
            "strategy",
            "roadmapping",
            "leadership",
            "cross-functional collaboration",
            "decision making",
            "communication",
        ],
        "domains": [
            "leadership",
            "communication",
            "cognitive",
        ],
        "threshold": 2,
    },

    "engineering manager": {
        "skills": [
            "leadership",
            "people management",
            "strategic thinking",
            "decision making",
            "communication",
        ],
        "domains": [
            "leadership",
            "communication",
        ],
        "threshold": 2,
    },

    "sales professional": {
        "skills": [
            "communication",
            "persuasion",
            "relationship management",
            "collaboration",
        ],
        "domains": [
            "communication",
            "personality",
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
        "coding",
        "software",
        "engineering",
        "developer",
        "algorithms",
        "programming",
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
            str(x) for x in text
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

        # IMPORTANT FIX:
        # NEVER CLEAN URLS

        if not raw_name or not raw_url:
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

        seen_names.add(
            normalized_name
        )

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

        source_text = normalize_text(
            " ".join(
                [
                    raw_name,
                    description,
                    " ".join(keys),
                    " ".join(job_levels),
                    " ".join(languages),
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

        all_traits = (
            technical_skills
            + cognitive_traits
            + personality_traits
            + leadership_traits
            + communication_skills
            + situational_traits
        )

        expanded_competencies = (
            expand_competencies(
                all_traits
            )
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
                infer_domains(source_text),

            "roles":
                infer_roles(source_text),

            "job_levels":
                job_levels,

            "languages":
                languages,

            "duration":
                clean_text(
                    item.get(
                        "duration",
                        "",
                    )
                ),

            "remote":
                clean_text(
                    item.get(
                        "remote",
                        "",
                    )
                ),

            "adaptive":
                clean_text(
                    item.get(
                        "adaptive",
                        "",
                    )
                ),

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

            "recommended_seniority":
                infer_seniority(source_text),

            "intents":
                infer_intents(source_text),
        }

        record["test_type"] = (
            infer_test_type(record)
        )

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
        }

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