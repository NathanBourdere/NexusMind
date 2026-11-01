import json
from unittest.mock import Mock

import pytest
import requests
from test_coach import draft, evidence

from nexusmind.infrastructure.gemini import GeminiGenerator


def session(status=200):
    response = Mock(status_code=status)
    response.json.return_value = {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {"text": draft(evidence().passages[0].id).model_dump_json()},
                    ]
                },
            }
        ],
    }
    return Mock(post=Mock(return_value=response))


def test_single_bounded_request_keeps_key_out_of_url_and_prompt():
    transport = session()
    result = GeminiGenerator("PRIVATE_KEY", session=transport).generate(evidence(), "beginner")
    assert result.status == "answered"
    transport.post.assert_called_once()
    args, kwargs = transport.post.call_args
    assert "PRIVATE_KEY" not in args[0]
    assert args[0].endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert "PRIVATE_KEY" not in json.dumps(kwargs["json"])
    assert kwargs["headers"]["x-goog-api-key"] == "PRIVATE_KEY"
    assert kwargs["timeout"] == (5, 90)
    assert kwargs["allow_redirects"] is False
    config = kwargs["json"]["generationConfig"]
    assert config["maxOutputTokens"] <= 2048
    assert config["responseMimeType"] == "application/json"
    assert config["thinkingConfig"] == {"thinkingLevel": "MINIMAL"}
    assert "tools" not in kwargs["json"]


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_upstream_error_has_no_retry_and_does_not_expose_body(status):
    transport = session(status)
    with pytest.raises(RuntimeError) as error:
        GeminiGenerator("SECRET", session=transport).generate(evidence(), "beginner")
    assert "SECRET" not in str(error.value)
    if status != 429:
        assert error.value.status_code == status
    transport.post.assert_called_once()


@pytest.mark.parametrize("reason", ["MAX_TOKENS", "SAFETY"])
def test_truncated_or_blocked_output_is_rejected(reason):
    transport = session()
    payload = transport.post.return_value.json.return_value
    payload["candidates"][0]["finishReason"] = reason
    with pytest.raises(RuntimeError):
        GeminiGenerator("SECRET", session=transport).generate(evidence(), "beginner")


def test_timeout_is_sanitized_without_retry():
    transport = Mock(post=Mock(side_effect=requests.Timeout("SECRET")))
    with pytest.raises(RuntimeError) as error:
        GeminiGenerator("SECRET", session=transport).generate(evidence(), "beginner")
    assert "SECRET" not in str(error.value)
    transport.post.assert_called_once()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"candidates": []},
        {
            "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "not JSON"}]}}],
        },
    ],
)
def test_malformed_provider_response_is_rejected(payload):
    transport = session()
    transport.post.return_value.json.return_value = payload
    with pytest.raises(RuntimeError):
        GeminiGenerator("SECRET", session=transport).generate(evidence(), "beginner")


def test_explicit_flash_model_keeps_its_supported_thinking_level():
    transport = session()
    generator = GeminiGenerator("SECRET", session=transport, model="gemini-3.8-flash")
    generator.generate(evidence(), "beginner")
    args, kwargs = transport.post.call_args
    assert args[0].endswith("/models/gemini-3.8-flash:generateContent")
    assert kwargs["json"]["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "LOW"}


def test_unknown_model_fails_before_network():
    transport = session()
    with pytest.raises(ValueError, match="Unsupported coach model"):
        GeminiGenerator("SECRET", session=transport, model="unknown-paid-model")
    transport.post.assert_not_called()
