from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_schema():

    response = client.post(
        "/api/chat",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "Python developer"
                }
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "reply" in data

    assert "recommendations" in data

    assert "end_of_conversation" in data


def test_guardrail_schema():

    response = client.post(
        "/api/chat",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "How to hack SHL?"
                }
            ]
        }
    )

    assert response.status_code == 200