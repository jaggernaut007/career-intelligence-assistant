"""
Rate Limiter.

Implements rate limiting per session to prevent abuse.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Optional

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# Slowapi limiter for use with FastAPI route decorators
# Uses IP-based rate limiting with session fallback
slowapi_limiter = Limiter(key_func=get_remote_address)


@dataclass
class RateLimitEntry:
    """Tracks rate limit state for a single session."""
    request_count: int = 0
    window_start: float = field(default_factory=time.time)
    last_request: float = field(default_factory=time.time)


class RateLimiter:
    """
    In-memory rate limiter with configurable limits per session.

    Features:
    - Sliding window rate limiting
    - Per-session tracking
    - Thread-safe operations
    - Automatic window reset
    """

    def __init__(
        self,
        limit: int = 10,
        window_seconds: int = 60,
    ):
        """
        Initialize rate limiter.

        Args:
            limit: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self._entries: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = Lock()

    def check(self, session_id: str) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            session_id: Session identifier

        Returns:
            True if request is allowed, False if rate limited
        """
        with self._lock:
            current_time = time.time()
            entry = self._entries[session_id]

            # Check if window has expired
            if current_time - entry.window_start >= self.window_seconds:
                # Reset window
                entry.request_count = 0
                entry.window_start = current_time

            # Check if under limit
            if entry.request_count < self.limit:
                entry.request_count += 1
                entry.last_request = current_time
                return True
            else:
                logger.warning(
                    f"Rate limit exceeded for session {session_id}: "
                    f"{entry.request_count}/{self.limit} requests"
                )
                return False

    def get_retry_after(self, session_id: str) -> Optional[float]:
        """
        Get seconds until rate limit resets.

        Args:
            session_id: Session identifier

        Returns:
            Seconds until window resets, or None if not rate limited
        """
        with self._lock:
            if session_id not in self._entries:
                return None

            entry = self._entries[session_id]
            current_time = time.time()
            time_in_window = current_time - entry.window_start

            if entry.request_count >= self.limit and time_in_window < self.window_seconds:
                return self.window_seconds - time_in_window

            return None

    def get_remaining(self, session_id: str) -> int:
        """
        Get remaining requests in current window.

        Args:
            session_id: Session identifier

        Returns:
            Number of remaining requests allowed
        """
        with self._lock:
            if session_id not in self._entries:
                return self.limit

            entry = self._entries[session_id]
            current_time = time.time()

            # Check if window has expired
            if current_time - entry.window_start >= self.window_seconds:
                return self.limit

            return max(0, self.limit - entry.request_count)

    def reset(self, session_id: str) -> None:
        """
        Reset rate limit for a session.

        Args:
            session_id: Session identifier
        """
        with self._lock:
            if session_id in self._entries:
                del self._entries[session_id]

    def reset_all(self) -> None:
        """Reset all rate limit entries."""
        with self._lock:
            self._entries.clear()

    def get_stats(self, session_id: str) -> Dict:
        """
        Get rate limit statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dict with rate limit stats
        """
        with self._lock:
            entry = self._entries.get(session_id)

            if not entry:
                return {
                    "session_id": session_id,
                    "request_count": 0,
                    "limit": self.limit,
                    "remaining": self.limit,
                    "window_seconds": self.window_seconds,
                    "retry_after": None,
                }

            current_time = time.time()
            time_in_window = current_time - entry.window_start

            # Check if window has expired
            if time_in_window >= self.window_seconds:
                return {
                    "session_id": session_id,
                    "request_count": 0,
                    "limit": self.limit,
                    "remaining": self.limit,
                    "window_seconds": self.window_seconds,
                    "retry_after": None,
                }

            remaining = max(0, self.limit - entry.request_count)
            retry_after = None if remaining > 0 else (self.window_seconds - time_in_window)

            return {
                "session_id": session_id,
                "request_count": entry.request_count,
                "limit": self.limit,
                "remaining": remaining,
                "window_seconds": self.window_seconds,
                "retry_after": retry_after,
            }


# Default rate limiter instance
_default_limiter: Optional[RateLimiter] = None


def get_rate_limiter(
    limit: int = 10,
    window_seconds: int = 60
) -> RateLimiter:
    """
    Get the default rate limiter instance.

    Args:
        limit: Maximum requests per window (only used on first call)
        window_seconds: Time window in seconds (only used on first call)

    Returns:
        RateLimiter instance
    """
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter(limit=limit, window_seconds=window_seconds)
    return _default_limiter
