from app.services.validation_service import (
    validate_messages
)


def test_valid_messages():

    messages = [
        {
            "role": "user",
            "content": "Python developer"
        }
    ]

    result = validate_messages(messages)

    assert result is True


def test_invalid_role():

    messages = [
        {
            "role": "invalid",
            "content": "Hello"
        }
    ]

    result = validate_messages(messages)

    assert result is False


def test_missing_content():

    messages = [
        {
            "role": "user"
        }
    ]

    result = validate_messages(messages)

    assert result is False


def test_empty_messages():

    result = validate_messages([])

    assert result is False