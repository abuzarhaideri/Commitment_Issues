"""Dependency-free pacing and sanitized provider rate-limit metadata."""
from __future__ import annotations

import json
import math
import re
import time
from datetime import timezone
from email.utils import parsedate_to_datetime

from harness.models import ModelError


class RateLimitError(ModelError):
    def __init__(self, message: str = "Model request rate limited", retry_after: float | None = None, terminal_quota: bool = False):
        super().__init__(message)
        self.retry_after = retry_after
        self.terminal_quota = terminal_quota
        self.input_tokens = self.output_tokens = 0
        self.usage_estimated = True


def _seconds(value) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) and result >= 0 else None


class RequestPacer:
    """Space request starts and bound waits by a caller's monotonic deadline."""

    def __init__(self, min_interval_seconds: float = 12, timeout_budget_seconds: float = 120, clock=time.monotonic, sleeper=time.sleep):
        interval = _seconds(min_interval_seconds)
        budget = _seconds(timeout_budget_seconds)
        if interval is None or budget is None or budget == 0:
            raise ValueError("Pacing interval must be nonnegative and timeout budget positive and finite")
        self.min_interval_seconds = interval
        self.timeout_budget_seconds = budget
        self.clock = clock
        self.sleeper = sleeper
        self._last_request: float | None = None

    def _wait(self, delay: float, deadline: float) -> None:
        if not math.isfinite(deadline) or delay >= deadline - self.clock():
            raise RateLimitError("Rate-limit wait exceeds timeout budget", retry_after=delay, terminal_quota=True)
        if delay:
            self.sleeper(delay)
        if self.clock() >= deadline:
            raise RateLimitError("Request timeout budget exhausted", terminal_quota=True)

    def before_request(self, deadline: float) -> None:
        now = self.clock()
        delay = 0.0 if self._last_request is None else max(0.0, self._last_request + self.min_interval_seconds - now)
        self._wait(delay, deadline)
        self._last_request = self.clock()

    def backoff(self, attempt: int, retry_after: float | None, deadline: float) -> float:
        if type(attempt) is not int or attempt < 0:
            raise ValueError("Retry attempt must be a nonnegative integer")
        delay = max(_seconds(retry_after) or 0.0, float(2 ** attempt) if attempt < 6 else 60.0)
        self._wait(delay, deadline)
        return delay


def retry_delay(headers, body_bytes: bytes) -> tuple[float | None, bool]:
    """Read Retry-After and Google RPC details without retaining response text."""
    delays = []
    retry_after = None
    if headers is not None:
        try:
            retry_after = next((value for key, value in headers.items() if key.lower() == "retry-after"), None)
        except (AttributeError, TypeError):
            pass
    numeric = _seconds(retry_after)
    if numeric is not None:
        delays.append(numeric)
    elif isinstance(retry_after, str):
        try:
            date = parsedate_to_datetime(retry_after)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            delays.append(max(0.0, date.timestamp() - time.time()))
        except (ValueError, TypeError, OverflowError):
            pass
    terminal = False
    try:
        body = json.loads(body_bytes)
        error = body.get("error", {}) if isinstance(body, dict) else {}
        details = error.get("details", []) if isinstance(error, dict) else []
        if not isinstance(details, list):
            details = []
        for detail in details:
            if not isinstance(detail, dict):
                continue
            kind = detail.get("@type", "")
            if not isinstance(kind, str):
                continue
            if kind.endswith("google.rpc.RetryInfo"):
                duration = detail.get("retryDelay")
                if isinstance(duration, str) and re.fullmatch(r"\d+(?:\.\d+)?s", duration):
                    seconds = _seconds(duration[:-1])
                    if seconds is not None:
                        delays.append(seconds)
            elif kind.endswith("google.rpc.QuotaFailure"):
                violations = detail.get("violations", [])
                if not isinstance(violations, list):
                    continue
                for violation in violations:
                    if isinstance(violation, dict):
                        for key in ("quotaId", "quotaMetric"):
                            value = violation.get(key)
                            if isinstance(value, str) and any(token in value.lower() for token in ("perday", "per_day", "per day", "daily")):
                                terminal = True
    except (ValueError, TypeError, UnicodeError):
        pass
    return (max(delays) if delays else None), terminal
