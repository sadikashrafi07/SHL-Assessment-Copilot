from app.services.recommendation import (
    generate_recommendations
)


def test_empty_recommendations():

    result = generate_recommendations(
        query="Python developer",
        context={}
    )

    assert isinstance(result, list)


def test_recommendation_limit():

    result = generate_recommendations(
        query="Java developer",
        context={}
    )

    assert len(result) <= 10