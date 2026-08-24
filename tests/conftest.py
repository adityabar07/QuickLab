"""
QuickLab — Pytest Shared Fixtures & Test Setup
"""

import pytest
from server.security import rate_limiter

@pytest.fixture(autouse=True)
def clean_rate_limiter_state():
    """Resets sliding window rate limiter state between tests."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()
