"""Token bucket rate limiter for Reddit API."""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for controlling API request rates.

    Reddit JSON API limits (no auth):
    - ~60 requests per minute
    - Recommended: 1 request per second

    This implementation uses a simple interval-based approach
    that ensures consistent spacing between requests.
    """

    def __init__(
        self,
        requests_per_minute: int = 30,
        min_interval: float = 0.5,
    ):
        """Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute.
            min_interval: Minimum seconds between requests.
        """
        self.requests_per_minute = requests_per_minute
        self.interval = max(60.0 / requests_per_minute, min_interval)
        self.last_request: float = 0
        self._lock: Optional[asyncio.Lock] = None

    @property
    def lock(self) -> asyncio.Lock:
        """Get or create the async lock."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def acquire(self) -> None:
        """Wait until it's safe to make a request.

        This method should be called before each API request.
        It will block until enough time has passed since the last request.
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_request
            wait_time = self.interval - elapsed

            if wait_time > 0:
                await asyncio.sleep(wait_time)

            self.last_request = time.time()

    def acquire_sync(self) -> None:
        """Synchronous version of acquire for non-async contexts.

        This method should be called before each API request.
        It will block until enough time has passed since the last request.
        """
        now = time.time()
        elapsed = now - self.last_request
        wait_time = self.interval - elapsed

        if wait_time > 0:
            time.sleep(wait_time)

        self.last_request = time.time()

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self.last_request = 0

    def get_wait_time(self) -> float:
        """Get the current wait time before next request can be made.

        Returns:
            Seconds to wait, or 0 if a request can be made immediately.
        """
        elapsed = time.time() - self.last_request
        wait_time = self.interval - elapsed
        return max(0, wait_time)

    def __repr__(self) -> str:
        return (
            f"RateLimiter(requests_per_minute={self.requests_per_minute}, "
            f"interval={self.interval:.2f}s)"
        )


class AdaptiveRateLimiter(RateLimiter):
    """Rate limiter that adapts based on API response headers.

    Reddit returns rate limit info in response headers:
    - X-Ratelimit-Remaining: Requests remaining in window
    - X-Ratelimit-Reset: Seconds until window resets
    - X-Ratelimit-Used: Requests used in current window
    """

    def __init__(
        self,
        requests_per_minute: int = 30,
        min_interval: float = 0.5,
        safety_margin: float = 0.8,
    ):
        """Initialize the adaptive rate limiter.

        Args:
            requests_per_minute: Default maximum requests per minute.
            min_interval: Minimum seconds between requests.
            safety_margin: Fraction of remaining quota to use (0-1).
        """
        super().__init__(requests_per_minute, min_interval)
        self.safety_margin = safety_margin
        self.remaining: Optional[int] = None
        self.reset_time: Optional[float] = None

    def update_from_headers(self, headers: dict) -> None:
        """Update rate limit state from response headers.

        Args:
            headers: Response headers from Reddit API.
        """
        remaining = headers.get("X-Ratelimit-Remaining")
        reset = headers.get("X-Ratelimit-Reset")

        if remaining is not None:
            self.remaining = int(float(remaining))

        if reset is not None:
            self.reset_time = time.time() + int(float(reset))

    async def acquire(self) -> None:
        """Wait until it's safe to make a request.

        Uses adaptive timing based on remaining quota if available.
        """
        async with self.lock:
            now = time.time()

            # Check if we have rate limit info from headers
            if self.remaining is not None and self.reset_time is not None:
                time_to_reset = self.reset_time - now

                if time_to_reset > 0 and self.remaining > 0:
                    # Calculate adaptive interval
                    safe_remaining = int(self.remaining * self.safety_margin)
                    if safe_remaining > 0:
                        adaptive_interval = time_to_reset / safe_remaining
                        interval = max(adaptive_interval, self.interval)
                    else:
                        interval = time_to_reset  # Wait for reset
                else:
                    interval = self.interval
            else:
                interval = self.interval

            elapsed = now - self.last_request
            wait_time = interval - elapsed

            if wait_time > 0:
                await asyncio.sleep(wait_time)

            self.last_request = time.time()

    def get_status(self) -> dict:
        """Get current rate limiter status.

        Returns:
            Dictionary with status information.
        """
        return {
            "interval": self.interval,
            "remaining": self.remaining,
            "reset_in": (
                max(0, self.reset_time - time.time())
                if self.reset_time
                else None
            ),
            "wait_time": self.get_wait_time(),
        }
