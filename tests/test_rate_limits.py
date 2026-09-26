import json
import unittest
from unittest.mock import patch

from harness.models import ModelError
from harness.rate_limits import RateLimitError, RequestPacer, retry_delay


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class RateLimitsTests(unittest.TestCase):
    def test_error_fields(self):
        error = RateLimitError(retry_after=12, terminal_quota=True)
        self.assertIsInstance(error, ModelError)
        self.assertEqual(error.retry_after, 12)
        self.assertTrue(error.terminal_quota)

    def test_paces_consecutive_request_starts(self):
        clock = FakeClock()
        pacer = RequestPacer(clock=clock, sleeper=clock.sleep)
        pacer.before_request(100)
        clock.now = 3
        pacer.before_request(100)
        pacer.before_request(100)
        self.assertEqual(clock.sleeps, [9, 12])
        self.assertEqual(clock.now, 24)

    def test_backoff_provider_delay_and_cap(self):
        clock = FakeClock()
        pacer = RequestPacer(clock=clock, sleeper=clock.sleep)
        self.assertEqual(pacer.backoff(2, 12, 500), 12)
        self.assertEqual(pacer.backoff(10000, None, 500), 60)
        self.assertEqual(pacer.backoff(0, None, 500), 1)
        self.assertEqual(clock.sleeps, [12, 60, 1])

    def test_deadline_fails_before_sleep(self):
        clock = FakeClock()
        pacer = RequestPacer(clock=clock, sleeper=clock.sleep)
        pacer.before_request(100)
        for action in (lambda: pacer.before_request(12), lambda: pacer.backoff(3, None, 8)):
            with self.assertRaises(RateLimitError) as caught:
                action()
            self.assertTrue(caught.exception.terminal_quota)
        self.assertEqual(clock.sleeps, [])
        with self.assertRaises(RateLimitError):
            RequestPacer(clock=clock, sleeper=clock.sleep).before_request(0)

    def test_retry_after_numeric_and_date(self):
        self.assertEqual(retry_delay({"retry-after": "12.5"}, b""), (12.5, False))
        with patch("harness.rate_limits.time.time", return_value=0):
            self.assertEqual(retry_delay({"Retry-After": "Thu, 01 Jan 1970 00:00:12 GMT"}, b"{}"), (12, False))

    def test_google_metadata(self):
        body = {"error": {"details": [
            {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "12s"},
            {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": "RequestsPerDay"}]},
        ]}}
        self.assertEqual(retry_delay({}, json.dumps(body).encode()), (12, True))
        self.assertEqual(retry_delay({"Retry-After": "20"}, json.dumps(body).encode()), (20, True))

    def test_daily_quota_spellings(self):
        for value in ("requests_per_day", "Requests per day", "daily_requests"):
            body = {"error": {"details": [{"@type": "google.rpc.QuotaFailure", "violations": [{"quotaMetric": value}]}]}}
            self.assertEqual(retry_delay({}, json.dumps(body).encode()), (None, True))

    def test_malformed_data_is_ignored(self):
        for body in (b"secret raw body", b"\xff", b"[]", b'{"error":null}', b'{"error":{"details":[null,{}, {"@type":null}]}}'):
            self.assertEqual(retry_delay({"Retry-After": "garbage"}, body), (None, False))
        for value in ("NaN", "inf", "-1"):
            self.assertEqual(retry_delay({"Retry-After": value}, b"{}"), (None, False))


if __name__ == "__main__":
    unittest.main()
