from app.services.conversation import (
    build_conversation_response
)


def test_empty_conversation():

    result = build_conversation_response(
        messages=[]
    )

    assert "reply" in result


def test_conversation_response_schema():

    result = build_conversation_response(
        messages=[
            {
                "role": "user",
                "content": "Python developer"
            }
        ]
    )

    assert "reply" in result

    assert "recommendations" in result

    assert "end_of_conversation" in result