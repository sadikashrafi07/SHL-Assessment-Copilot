from app.services.query_parser import (
    parse_query
)


def test_parse_technical():

    result = parse_query(
        "Python developer assessment"
    )

    assert result["technical"] is True


def test_parse_personality():

    result = parse_query(
        "personality assessment"
    )

    assert result["personality"] is True


def test_parse_leadership():

    result = parse_query(
        "leadership hiring"
    )

    assert result["leadership"] is True


def test_parse_cognitive():

    result = parse_query(
        "cognitive reasoning test"
    )

    assert result["cognitive"] is True


def test_parse_empty():

    result = parse_query("")

    assert isinstance(result, dict)