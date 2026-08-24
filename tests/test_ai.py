import pytest
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

def test_ai_explain_endpoint_safety():
    code = "import numpy as np\nx = np.linspace(0, 10, 100)"
    res = client.post("/api/ai/explain", json={"code": code, "context": "Plotting curve"})
    
    # If GEMINI_API_KEY is not set in test environment, it must return a safe 400 error
    if not settings.GEMINI_API_KEY:
        assert res.status_code == 400
        assert "GEMINI_API_KEY" in res.json().get("detail", "")
    else:
        assert res.status_code in (200, 503)

def test_ai_fix_error_endpoint_safety():
    code = "print(undefined_var)"
    error = "NameError: name 'undefined_var' is not defined"
    res = client.post("/api/ai/fix-error", json={"code": code, "error": error})
    
    if not settings.GEMINI_API_KEY:
        assert res.status_code == 400
        assert "GEMINI_API_KEY" in res.json().get("detail", "")
    else:
        assert res.status_code in (200, 503)

def test_ai_generate_endpoint_safety():
    prompt = "Create a pandas dataframe with 5 random integers"
    res = client.post("/api/ai/generate", json={"prompt": prompt})
    
    if not settings.GEMINI_API_KEY:
        assert res.status_code == 400
        assert "GEMINI_API_KEY" in res.json().get("detail", "")
    else:
        assert res.status_code in (200, 503)

def test_ai_input_validation():
    # Null byte in code
    res1 = client.post("/api/ai/explain", json={"code": "print('hello\x00world')"})
    assert res1.status_code == 400
    assert "null" in res1.json().get("detail", "").lower()

    # Oversized prompt (> 2000 chars)
    res2 = client.post("/api/ai/generate", json={"prompt": "A" * 3000})
    assert res2.status_code in (400, 422)

def test_ai_rate_limiting():
    # Rapidly send requests to trigger AI rate limiting
    hit_429 = False
    for _ in range(settings.RATE_LIMIT_AI_PER_MIN + 5):
        res = client.post("/api/ai/explain", json={"code": "x = 1"})
        if res.status_code == 429:
            hit_429 = True
            assert "Retry-After" in res.headers
            break
    assert hit_429 is True, "AI rate limiter must return HTTP 429 when quota/rate exceeded."
