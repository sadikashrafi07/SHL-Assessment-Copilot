from app.services.guardrails import (
    is_safe_query
)


def test_block_hack():

    result = is_safe_query(
        "How to hack SHL?"
    )

    assert result is False


def test_block_crypto():

    result = is_safe_query(
        "Best crypto investment?"
    )

    assert result is False


def test_allow_valid_query():

    result = is_safe_query(
        "Need Python assessment"
    )

    assert result is True


def test_empty_query():

    result = is_safe_query("")

    assert result is True