import json
import re

CATALOG_PATH = "data/cleaned_catalog.json"


with open(CATALOG_PATH, "r") as f:
    CATALOG = json.load(f)


COMPARISON_KEYWORDS = [
    "compare",
    "difference",
    "vs",
    "versus"
]


def extract_comparison_targets(user_message: str):

    text = user_message.lower()

    if " vs " in text:
        parts = text.split(" vs ")

    elif " versus " in text:
        parts = text.split(" versus ")

    else:
        cleaned = text

        for keyword in COMPARISON_KEYWORDS:
            cleaned = cleaned.replace(keyword, "")

        parts = re.split(r",|and", cleaned)

    targets = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    return targets[:2]


def find_assessment_by_name(name: str):

    for item in CATALOG:

        if name.lower() in item["name"].lower():
            return item

    return None


def compare_assessments(user_message: str):

    targets = extract_comparison_targets(
        user_message
    )

    if len(targets) < 2:
        return (
            "Please specify two SHL assessments to compare."
        )

    first = find_assessment_by_name(targets[0])
    second = find_assessment_by_name(targets[1])

    if not first or not second:
        return (
            "I could not find both assessments in the SHL catalog."
        )

    comparison = f"""
Assessment Comparison

1. {first['name']}
- Test Type: {first['test_type']}
- Duration: {first.get('duration', 'Unknown')}
- Competencies: {', '.join(first.get('keys', []))}
- URL: {first['url']}

2. {second['name']}
- Test Type: {second['test_type']}
- Duration: {second.get('duration', 'Unknown')}
- Competencies: {', '.join(second.get('keys', []))}
- URL: {second['url']}

Key Difference:
{first['name']} is more focused on {', '.join(first.get('keys', [])[:3])}, while {second['name']} emphasizes {', '.join(second.get('keys', [])[:3])}.
"""

    return comparison.strip()