from app.services.retrieval import (
    retrieve_assessments
)


def test_empty_query():

    result = retrieve_assessments("")

    assert isinstance(result, list)


def test_python_query():

    result = retrieve_assessments(
        "Python developer assessment"
    )

    assert isinstance(result, list)


def test_top_k_limit():

    result = retrieve_assessments(
        "Java assessment"
    )

    assert len(result) <= 10