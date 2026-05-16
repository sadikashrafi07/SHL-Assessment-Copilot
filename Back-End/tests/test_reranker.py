# =========================================================
# TEST RERANKER
# File: tests/test_reranker.py
# =========================================================

import pytest

from app.services.reranker import rerank_results


# =========================================================
# TEST DATA HELPERS
# =========================================================

def build_item(
    name,
    description,
    test_type,
    keys=None,
    remote="No",
    adaptive="No",
    duration="45 minutes"
):

    return {

        "name": name,

        "description": description,

        "test_type": test_type,

        "keys": keys or [],

        "remote": remote,

        "adaptive": adaptive,

        "duration": duration,

        "job_levels": ["Mid"],

        "url": (
            "https://www.shl.com/"
            f"{name.lower().replace(' ', '-')}"
        )
    }


# =========================================================
# PYTHON PRIORITY TEST
# =========================================================

def test_python_ranking():

    results = [

        build_item(
            name="Python (New)",
            description=(
                "Python technical assessment "
                "for backend developers"
            ),
            test_type="Technical",
            keys=["python", "backend"]
        ),

        build_item(
            name="Java Assessment",
            description=(
                "Java technical test "
                "for enterprise developers"
            ),
            test_type="Technical",
            keys=["java"]
        )
    ]

    query = (
        "Python developer with stakeholder communication"
    )

    context = {

        "skills": ["Python"],

        "role": "Developer",

        "seniority": "Mid"
    }

    ranked = rerank_results(
        results=results,
        query=query,
        context=context
    )

    assert ranked

    assert ranked[0]["name"] == "Python (New)"

    assert ranked[0]["score"] >= ranked[1]["score"]


# =========================================================
# COMMUNICATION FILTER TEST
# =========================================================

def test_remove_irrelevant_communication():

    results = [

        build_item(
            name="Sales Communication",
            description=(
                "Sales email communication "
                "and telecalling assessment"
            ),
            test_type="Communication"
        ),

        build_item(
            name="Stakeholder Communication",
            description=(
                "Professional business "
                "communication assessment"
            ),
            test_type="Communication"
        )
    ]

    query = (
        "Python developer with "
        "stakeholder communication"
    )

    context = {
        "skills": ["Python"]
    }

    ranked = rerank_results(
        results=results,
        query=query,
        context=context
    )

    names = [
        item["name"]
        for item in ranked
    ]

    assert (
        "Sales Communication"
        not in names
    )

    assert (
        "Stakeholder Communication"
        in names
    )


# =========================================================
# DUPLICATE REMOVAL TEST
# =========================================================

def test_duplicate_removal():

    results = [

        build_item(
            name="Python Test",
            description="Python coding test",
            test_type="Technical"
        ),

        build_item(
            name="Python Test",
            description="Duplicate test",
            test_type="Technical"
        )
    ]

    query = "Python developer"

    context = {
        "skills": ["Python"]
    }

    ranked = rerank_results(
        results=results,
        query=query,
        context=context
    )

    names = [
        item["name"]
        for item in ranked
    ]

    assert len(names) == len(set(names))

    assert len(ranked) == 1


# =========================================================
# TECHNICAL FILTER TEST
# =========================================================

def test_technical_query_filters_non_technical():

    results = [

        build_item(
            name="Python Coding Test",
            description="Technical coding challenge",
            test_type="Technical"
        ),

        build_item(
            name="Personality Profile",
            description="Behavioral personality test",
            test_type="Personality"
        )
    ]

    query = (
        "Python backend developer assessment"
    )

    context = {
        "skills": ["Python"],
        "role": "Developer"
    }

    ranked = rerank_results(
        results=results,
        query=query,
        context=context
    )

    assert ranked

    assert all(
        item["test_type"].lower()
        == "technical"
        for item in ranked
    )


# =========================================================
# REMOTE BOOST TEST
# =========================================================

def test_remote_assessment_boost():

    results = [

        build_item(
            name="Remote Python Test",
            description="Remote Python coding assessment",
            test_type="Technical",
            remote="Yes"
        ),

        build_item(
            name="Offline Python Test",
            description="Python assessment",
            test_type="Technical",
            remote="No"
        )
    ]

    query = (
        "Remote Python developer assessment"
    )

    context = {
        "skills": ["Python"]
    }

    ranked = rerank_results(
        results=results,
        query=query,
        context=context
    )

    assert ranked[0]["name"] == "Remote Python Test"


# =========================================================
# ADAPTIVE BOOST TEST
# =========================================================

def test_adaptive_assessment_boost():

    results = [

        build_item(
            name="Adaptive Python Test",
            description="Adaptive Python coding assessment",
            test_type="Technical",
            adaptive="Yes"
        ),

        build_item(
            name="Static Python Test",
            description="Static coding test",
            test_type="Technical",
            adaptive="No"
        )
    ]

    query = (
        "Adaptive Python assessment"
    )

    context = {
        "skills": ["Python"]
    }

    ranked = rerank_results(
        results=results,
        query=query,
        context=context
    )

    assert ranked[0]["name"] == "Adaptive Python Test"


# =========================================================
# SHORT DURATION TEST
# =========================================================

def test_short_duration_priority():

    results = [

        build_item(
            name="Quick Python Test",
            description="Fast coding assessment",
            test_type="Technical",
            duration="25 minutes"
        ),

        build_item(
            name="Long Python Test",
            description="Comprehensive coding assessment",
            test_type="Technical",
            duration="60 minutes"
        )
    ]

    query = (
        "Python assessment under 30 minutes"
    )

    context = {
        "skills": ["Python"]
    }

    ranked = rerank_results(
        results=results,
        query=query,
        context=context
    )

    assert ranked[0]["name"] == "Quick Python Test"


# =========================================================
# EMPTY RESULTS TEST
# =========================================================

def test_empty_results():

    ranked = rerank_results(
        results=[],
        query="Python developer",
        context={}
    )

    assert ranked == []


# =========================================================
# INVALID INPUT SAFETY TEST
# =========================================================

def test_invalid_input_safety():

    ranked = rerank_results(
        results=[None, {}, []],
        query="Python developer",
        context={}
    )

    assert isinstance(ranked, list)


# =========================================================
# CONFIDENCE SCORE TEST
# =========================================================

def test_confidence_scores_exist():

    results = [

        build_item(
            name="Python Assessment",
            description="Python coding assessment",
            test_type="Technical"
        )
    ]

    ranked = rerank_results(
        results=results,
        query="Python developer",
        context={
            "skills": ["Python"]
        }
    )

    assert ranked

    assert "confidence" in ranked[0]

    assert isinstance(
        ranked[0]["confidence"],
        float
    )


# =========================================================
# SCORE BREAKDOWN TEST
# =========================================================

def test_score_breakdown_exists():

    results = [

        build_item(
            name="Python Assessment",
            description="Python coding assessment",
            test_type="Technical"
        )
    ]

    ranked = rerank_results(
        results=results,
        query="Python developer",
        context={
            "skills": ["Python"]
        }
    )

    assert ranked

    assert "score_breakdown" in ranked[0]

    assert isinstance(
        ranked[0]["score_breakdown"],
        list
    )