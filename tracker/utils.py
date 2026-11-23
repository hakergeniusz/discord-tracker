"""Small pure helpers shared across the bot."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return an aware UTC datetime."""
    return datetime.now(UTC)


def format_timestamp(value: datetime) -> str:
    """Render a datetime as a compact, sortable ISO-8601 string."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="seconds")


def truncate(text: str, limit: int) -> str:
    """Cut ``text`` to ``limit`` characters, marking the cut when needed."""
    if limit < 1:
        raise ValueError("limit must be >= 1")
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3] + "..."


def format_duration(seconds: float) -> str:
    """Turn a number of seconds into a readable ``1d 2h 3m 4s`` string."""
    seconds = max(0, int(seconds))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts: list[str] = []
    for amount, unit in ((days, "d"), (hours, "h"), (minutes, "m"), (secs, "s")):
        if amount:
            parts.append(f"{amount}{unit}")
    return " ".join(parts) if parts else "0s"
