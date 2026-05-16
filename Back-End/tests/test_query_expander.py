from app.services.query_expander import (
    build_expansion_metadata
)


def test_query_expansion():

    result = build_expansion_metadata(
        "Python developer"
    )

    assert "expanded_query" in result


def test_weighted_terms():

    result = build_expansion_metadata(
        "Java engineer"
    )

    assert "weighted_terms" in result


def test_empty_query():

    result = build_expansion_metadata("")

    assert isinstance(result, dict)