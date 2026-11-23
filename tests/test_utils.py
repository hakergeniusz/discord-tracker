from datetime import UTC, datetime

import pytest

from tracker.utils import format_duration, format_timestamp, truncate


def test_truncate():
    assert truncate("hello", 10) == "hello"
    assert truncate("hello world", 8) == "hello..."
    assert truncate("abcdef", 3) == "abc"


def test_truncate_rejects_bad_limit():
    with pytest.raises(ValueError):
        truncate("hello", 0)


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "0s"), (5, "5s"), (65, "1m 5s"), (3661, "1h 1m 1s"), (90061, "1d 1h 1m 1s")],
)
def test_format_duration(seconds, expected):
    assert format_duration(seconds) == expected


def test_format_timestamp():
    aware = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert format_timestamp(aware) == "2026-01-02T03:04:05+00:00"


def test_format_timestamp_naive_is_utc():
    naive = datetime(2026, 1, 2, 3, 4, 5)
    assert format_timestamp(naive) == "2026-01-02T03:04:05+00:00"
