from typing import List, Dict


# =========================================================
# CLEAN REASON
# =========================================================

def clean_reason(reason: str) -> str:

    if not reason:
        return ""

    reason = reason.lstrip("+").strip()

    replacements = {

        "semantic":
            "semantic relevance",

        "technical":
            "technical assessment alignment",

        "communication":
            "communication assessment alignment",

        "personality":
            "personality assessment alignment",

        "leadership":
            "leadership capability alignment",

        "cognitive":
            "cognitive assessment alignment",

        "live coding":
            "live coding capability",

        "short duration":
            "short assessment duration",

        "remote":
            "remote testing support",

        "adaptive":
            "adaptive testing support",

        "python":
            "Python skill relevance",

        "java":
            "Java skill relevance"
    }

    for key, value in replacements.items():

        if key in reason:
            reason = reason.replace(
                key,
                value
            )

    return reason


# =========================================================
# SINGLE RECOMMENDATION EXPLANATION
# =========================================================

def generate_recommendation_reason(
    item: Dict
) -> str:

    score_breakdown = item.get(
        "score_breakdown",
        []
    )

    if not score_breakdown:

        return (
            "Recommended based on strong alignment "
            "with the hiring requirements."
        )

    positive_reasons = []

    for reason in score_breakdown:

        if not reason.startswith("+"):
            continue

        cleaned = clean_reason(reason)

        if cleaned:
            positive_reasons.append(cleaned)

    unique_reasons = list(
        dict.fromkeys(positive_reasons)
    )

    top_reasons = unique_reasons[:3]

    if not top_reasons:

        return (
            "Recommended due to overall assessment relevance."
        )

    return (
        "Recommended because of "
        + ", ".join(top_reasons)
        + "."
    )


# =========================================================
# SUMMARY
# =========================================================

def generate_summary(
    results: List[Dict]
) -> str:

    if not results:

        return (
            "No highly relevant SHL assessments were found."
        )

    top_result = results[0]

    top_name = top_result.get(
        "name",
        "the selected assessment"
    )

    test_type = top_result.get(
        "test_type",
        "General"
    )

    confidence = top_result.get(
        "confidence",
        0
    )

    return (
        f"Top recommendation is {top_name}, "
        f"a {test_type} assessment with "
        f"{round(confidence * 100)}% confidence."
    )


# =========================================================
# MULTI RESULT EXPLANATION
# =========================================================

def generate_combined_explanation(
    results: List[Dict]
) -> List[Dict]:

    enhanced_results = []

    for item in results:

        enhanced_item = item.copy()

        enhanced_item[
            "recommendation_reason"
        ] = generate_recommendation_reason(
            enhanced_item
        )

        enhanced_results.append(
            enhanced_item
        )

    return enhanced_results