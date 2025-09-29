import pytest
from unittest.mock import patch, MagicMock
from agent_core.mistral_api import MistralAPI, MistralAPIError, APIResponseModel
import os
import requests

@pytest.fixture
def mock_api_key():
    return "test_api_key_123"

@pytest.fixture
def mock_base_url():
    return "https://api.test.mistral.ai/v1"

@pytest.fixture
def mock_valid_response():
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677666992,
        "model": "mistral-large",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

@pytest.fixture
def mock_invalid_response():
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677666992,
        "model": "mistral-large",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response"
                },
                "finish_reason": "stop"
            }
        ],
        # Missing usage field to make it invalid
    }

@pytest.fixture
def mock_tool_response():
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677666992,
        "model": "mistral-large",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response",
                    "tool_calls": [
                        {
                            "id": "tool_01",
                            "type": "function",
                            "function": {
                                "name": "test_function",
                                "arguments": "{}"
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

def test_initialization_with_api_key(mock_api_key, mock_base_url):
    api = MistralAPI(api_key=mock_api_key, base_url=mock_base_url)
    assert api.api_key == mock_api_key
    assert api.base_url == mock_base_url

def test_initialization_with_env_var(monkeypatch, mock_base_url):
    monkeypatch.setenv("MISTRAL_API_KEY", "env_api_key_456")
    api = MistralAPI(base_url=mock_base_url)
    assert api.api_key == "env_api_key_456"

def test_initialization_no_api_key():
    with pytest.raises(ValueError):
        MistralAPI()

@patch("requests.Session.request")
def test_successful_request(mock_request, mock_api_key, mock_base_url, mock_valid_response):
    mock_request.return_value = MagicMock(status_code=200, json=lambda: mock_valid_response)

    api = MistralAPI(api_key=mock_api_key, base_url=mock_base_url)
    response = api._make_request("POST", "chat/completions", json={"test": "data"})

    assert isinstance(response, APIResponseModel)
    assert response.id == "chatcmpl-123"

@patch("requests.Session.request")
def test_invalid_response(mock_request, mock_api_key, mock_base_url, mock_invalid_response):
    mock_request.return_value = MagicMock(status_code=200, json=lambda: mock_invalid_response)

    api = MistralAPI(api_key=mock_api_key, base_url=mock_base_url)

    with pytest.raises(MistralAPIError):
        api._make_request("POST", "chat/completions", json={"test": "data"})

@patch("requests.Session.request")
def test_api_error(mock_request, mock_api_key, mock_base_url):
    mock_request.return_value = MagicMock(
        status_code=401,
        json=lambda: {"error": {"message": "Invalid API key"}}
    )

    api = MistralAPI(api_key=mock_api_key, base_url=mock_base_url)

    with pytest.raises(MistralAPIError):
        api._make_request("POST", "chat/completions", json={"test": "data"})

@patch("requests.Session.request")
def test_retry_mechanism(mock_request, mock_api_key, mock_base_url, mock_valid_response):
    # First two attempts fail, third succeeds
    side_effect = [
        requests.exceptions.ConnectionError("Connection failed"),
        requests.exceptions.Timeout("Request timed out"),
        MagicMock(status_code=200, json=lambda: mock_valid_response)
    ]
    mock_request.side_effect = side_effect

    api = MistralAPI(api_key=mock_api_key, base_url=mock_base_url)
    response = api._make_request("POST", "chat/completions", json={"test": "data"})

    assert isinstance(response, APIResponseModel)
    assert mock_request.call_count == 3

@patch("requests.Session.request")
def test_chat_completion(mock_request, mock_api_key, mock_base_url, mock_valid_response):
    mock_request.return_value = MagicMock(status_code=200, json=lambda: mock_valid_response)

    api = MistralAPI(api_key=mock_api_key, base_url=mock_base_url)
    response = api.chat_completion([{"role": "user", "content": "Hello"}])

    assert isinstance(response, APIResponseModel)
    assert response.id == "chatcmpl-123"
    # Verify JSON mode is used
    assert mock_request.call_args[1]["json"]["response_format"] == {"type": "json_object"}

def test_tool_invocation_detection(mock_tool_response):
    api = MistralAPI(api_key="test")
    assert api.detect_tool_invocation(mock_tool_response) is True

def test_no_tool_invocation(mock_valid_response):
    api = MistralAPI(api_key="test")
    assert api.detect_tool_invocation(mock_valid_response) is False