import re


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(text):
    """
    Universal normalization utility
    used across retrieval, ranking,
    parsing, and guardrails.
    """

    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    text = text.lower()

    # Remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_text(text):
    """
    Alias used by guardrails.
    """

    return normalize(text)


# =========================================================
# PATTERN MATCHING
# =========================================================

def contains_pattern(text, patterns):
    """
    Checks whether any normalized
    pattern exists in normalized text.
    """

    if not text:
        return False

    normalized_text = normalize(text)

    for pattern in patterns:

        if normalize(pattern) in normalized_text:
            return True

    return False


# =========================================================
# DURATION PARSER
# =========================================================

def extract_duration_minutes(duration_text):
    """
    Converts duration text into minutes.

    Supported:
    - 30 mins
    - 45 minutes
    - 1 hour
    - 1.5 hours
    - 2 hrs
    - 45m
    """

    if not duration_text:
        return 0

    normalized = normalize(duration_text)

    # =====================================
    # HOURS
    # =====================================

    hour_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(hour|hours|hr|hrs|h)",
        normalized
    )

    if hour_match:

        hours = float(
            hour_match.group(1)
        )

        return int(hours * 60)

    # =====================================
    # MINUTES
    # =====================================

    minute_match = re.search(
        r"(\d+)\s*(minute|minutes|min|mins|m)",
        normalized
    )

    if minute_match:

        return int(
            minute_match.group(1)
        )

    return 0


# =========================================================
# SAFE CASTING
# =========================================================

def safe_float(value):

    try:
        return float(value)

    except Exception:
        return 0.0


def safe_int(value):

    try:
        return int(value)

    except Exception:
        return 0


# =========================================================
# LIST CLEANER
# =========================================================

def clean_list(values):

    if not isinstance(values, list):
        return []

    cleaned = []

    for item in values:

        if item in [None, "", [], {}]:
            continue

        cleaned.append(item)

    return cleaned


# =========================================================
# DEDUPLICATION
# =========================================================

def deduplicate_by_key(items, key):
    """
    Removes duplicate dictionaries
    using normalized key values.
    """

    if not items:
        return []

    seen = set()

    results = []

    for item in items:

        value = normalize(
            item.get(key, "")
        )

        if not value:
            continue

        if value in seen:
            continue

        seen.add(value)

        results.append(item)

    return results