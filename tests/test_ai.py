import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from server.main import app
from server.config import settings

client = TestClient(app)

def test_ai_status_endpoint():
    res = client.get("/api/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data
    assert "model" in data

def test_ai_chat_endpoint_safety_and_mock():
    # Test valid chat request with mock
    with patch("server.services.gemini.gemini_service.generate_chat_response", return_value="Here is how you use Pandas DataFrames in QuickLab."):
        with patch("server.services.gemini.gemini_service.is_configured", return_value=True):
            res = client.post("/api/ai/chat", json={"message": "How do I create a Pandas DataFrame?"})
            assert res.status_code == 200
            data = res.json()
            assert "response" in data
            assert "Pandas DataFrames" in data["response"]
            # Ensure API key is never returned
            if settings.GEMINI_API_KEY:
                assert settings.GEMINI_API_KEY not in str(data)

def test_ai_chat_input_validation():
    # Empty message
    res_empty = client.post("/api/ai/chat", json={"message": ""})
    assert res_empty.status_code in (400, 422)

    # Missing message field
    res_missing = client.post("/api/ai/chat", json={})
    assert res_missing.status_code == 422

    # Null byte in message
    res_null = client.post("/api/ai/chat", json={"message": "Hello\x00world"})
    assert res_null.status_code == 400
    assert "Invalid message" in res_null.json().get("detail", "")

    # Oversized message (> 4000 chars)
    res_oversized = client.post("/api/ai/chat", json={"message": "A" * 5000})
    assert res_oversized.status_code == 422

def test_ai_chat_unconfigured_or_error_handling():
    # When unconfigured
    with patch("server.services.gemini.gemini_service.is_configured", return_value=False):
        res = client.post("/api/ai/chat", json={"message": "Hello"})
        assert res.status_code == 503
        assert "not configured" in res.json().get("detail", "")

    # When service throws an internal exception
    with patch("server.services.gemini.gemini_service.generate_chat_response", side_effect=RuntimeError("Internal failure")):
        with patch("server.services.gemini.gemini_service.is_configured", return_value=True):
            res = client.post("/api/ai/chat", json={"message": "Hello"})
            assert res.status_code == 503
            assert res.json().get("detail") == "AI service is temporarily unavailable."

def test_ai_explain_endpoint_safety():
    with patch("server.services.gemini.gemini_service.explain_code", return_value="This calculates a sequence."):
        with patch("server.services.gemini.gemini_service.is_configured", return_value=True):
            code = "import numpy as np\nx = np.linspace(0, 10, 100)"
            res = client.post("/api/ai/explain", json={"code": code, "context": "Plotting curve"})
            assert res.status_code == 200
            assert "explanation" in res.json()

def test_ai_fix_error_endpoint_safety():
    with patch("server.services.gemini.gemini_service.fix_error", return_value="Fixed code:\n```python\nprint('hello')\n```"):
        with patch("server.services.gemini.gemini_service.is_configured", return_value=True):
            code = "print(undefined_var)"
            error = "NameError: name 'undefined_var' is not defined"
            res = client.post("/api/ai/fix-error", json={"code": code, "error": error})
            assert res.status_code == 200
            assert "fix" in res.json()

def test_ai_generate_endpoint_safety():
    with patch("server.services.gemini.gemini_service.generate_code", return_value="```python\nimport pandas as pd\n```"):
        with patch("server.services.gemini.gemini_service.is_configured", return_value=True):
            prompt = "Create a pandas dataframe with 5 random integers"
            res = client.post("/api/ai/generate", json={"prompt": prompt})
            assert res.status_code == 200
            assert "code" in res.json()

def test_ai_rate_limiting():
    # Rapidly send requests to trigger AI rate limiting
    hit_429 = False
    for _ in range(settings.RATE_LIMIT_AI_PER_MIN + 5):
        res = client.post("/api/ai/chat", json={"message": "Ping"})
        if res.status_code == 429:
            hit_429 = True
            assert "Retry-After" in res.headers
            break
    assert hit_429 is True, "AI rate limiter must return HTTP 429 when rate limit exceeded."
