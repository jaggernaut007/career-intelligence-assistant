"""
Unit tests for Rate Limiter.

Tests the RateLimiter class and slowapi integration.
"""

import time
import pytest
from unittest.mock import MagicMock, patch


class TestRateLimiterClass:
    """Test suite for the custom RateLimiter class."""

    def test_rate_limiter_allows_requests_under_limit(self):
        """Requests under the limit should be allowed."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=10, window_seconds=60)
        session_id = "test-session-1"

        # First 10 requests should be allowed
        for i in range(10):
            assert limiter.check(session_id) is True

    def test_rate_limiter_blocks_requests_over_limit(self):
        """Requests over the limit should be blocked."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=5, window_seconds=60)
        session_id = "test-session-2"

        # Use up all allowed requests
        for _ in range(5):
            limiter.check(session_id)

        # Next request should be blocked
        assert limiter.check(session_id) is False

    def test_rate_limiter_resets_after_window(self):
        """Rate limit should reset after the time window expires."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=2, window_seconds=1)
        session_id = "test-session-3"

        # Use up all allowed requests
        assert limiter.check(session_id) is True
        assert limiter.check(session_id) is True
        assert limiter.check(session_id) is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        assert limiter.check(session_id) is True

    def test_rate_limiter_tracks_sessions_independently(self):
        """Each session should have its own rate limit counter."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=2, window_seconds=60)

        # Session 1 uses its limit
        assert limiter.check("session-1") is True
        assert limiter.check("session-1") is True
        assert limiter.check("session-1") is False

        # Session 2 should still have its full limit
        assert limiter.check("session-2") is True
        assert limiter.check("session-2") is True
        assert limiter.check("session-2") is False

    def test_get_remaining_returns_correct_count(self):
        """get_remaining should return the correct number of remaining requests."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=5, window_seconds=60)
        session_id = "test-session-4"

        assert limiter.get_remaining(session_id) == 5

        limiter.check(session_id)
        assert limiter.get_remaining(session_id) == 4

        limiter.check(session_id)
        limiter.check(session_id)
        assert limiter.get_remaining(session_id) == 2

    def test_get_retry_after_returns_none_when_not_limited(self):
        """get_retry_after should return None when not rate limited."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=5, window_seconds=60)
        session_id = "test-session-5"

        assert limiter.get_retry_after(session_id) is None

        limiter.check(session_id)
        assert limiter.get_retry_after(session_id) is None

    def test_get_retry_after_returns_seconds_when_limited(self):
        """get_retry_after should return seconds until reset when rate limited."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=1, window_seconds=60)
        session_id = "test-session-6"

        limiter.check(session_id)
        retry_after = limiter.get_retry_after(session_id)

        assert retry_after is not None
        assert 0 < retry_after <= 60

    def test_reset_clears_session_limit(self):
        """reset should clear the rate limit for a specific session."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=2, window_seconds=60)
        session_id = "test-session-7"

        # Use up all requests
        limiter.check(session_id)
        limiter.check(session_id)
        assert limiter.check(session_id) is False

        # Reset the session
        limiter.reset(session_id)

        # Should be allowed again
        assert limiter.check(session_id) is True

    def test_reset_all_clears_all_limits(self):
        """reset_all should clear all rate limits."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=1, window_seconds=60)

        # Use up limits for multiple sessions
        limiter.check("session-a")
        limiter.check("session-b")
        assert limiter.check("session-a") is False
        assert limiter.check("session-b") is False

        # Reset all
        limiter.reset_all()

        # All sessions should be allowed again
        assert limiter.check("session-a") is True
        assert limiter.check("session-b") is True

    def test_get_stats_returns_correct_data(self):
        """get_stats should return correct statistics."""
        from app.guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter(limit=5, window_seconds=60)
        session_id = "test-session-8"

        # Initial stats
        stats = limiter.get_stats(session_id)
        assert stats["request_count"] == 0
        assert stats["limit"] == 5
        assert stats["remaining"] == 5
        assert stats["retry_after"] is None

        # After some requests
        limiter.check(session_id)
        limiter.check(session_id)
        limiter.check(session_id)

        stats = limiter.get_stats(session_id)
        assert stats["request_count"] == 3
        assert stats["remaining"] == 2


class TestSlowApiLimiter:
    """Test suite for slowapi limiter integration."""

    def test_slowapi_limiter_is_exported(self):
        """slowapi_limiter should be importable from rate_limiter module."""
        from app.guardrails.rate_limiter import slowapi_limiter

        assert slowapi_limiter is not None

    def test_slowapi_limiter_is_limiter_instance(self):
        """slowapi_limiter should be a Limiter instance."""
        from slowapi import Limiter
        from app.guardrails.rate_limiter import slowapi_limiter

        assert isinstance(slowapi_limiter, Limiter)


class TestGetRateLimiter:
    """Test suite for get_rate_limiter singleton function."""

    def test_get_rate_limiter_returns_instance(self):
        """get_rate_limiter should return a RateLimiter instance."""
        from app.guardrails.rate_limiter import get_rate_limiter, RateLimiter

        # Reset the singleton for testing
        import app.guardrails.rate_limiter as rl_module
        rl_module._default_limiter = None

        limiter = get_rate_limiter()
        assert isinstance(limiter, RateLimiter)

    def test_get_rate_limiter_returns_same_instance(self):
        """get_rate_limiter should return the same instance on multiple calls."""
        from app.guardrails.rate_limiter import get_rate_limiter

        # Reset the singleton for testing
        import app.guardrails.rate_limiter as rl_module
        rl_module._default_limiter = None

        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2

    def test_get_rate_limiter_uses_default_values(self):
        """get_rate_limiter should use 10/minute by default."""
        from app.guardrails.rate_limiter import get_rate_limiter

        # Reset the singleton for testing
        import app.guardrails.rate_limiter as rl_module
        rl_module._default_limiter = None

        limiter = get_rate_limiter()

        assert limiter.limit == 10
        assert limiter.window_seconds == 60
