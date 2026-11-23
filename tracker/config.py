"""Environment driven configuration for the bot.

Everything that varies between deployments lives here so the code never has
to be edited to change behaviour. Values are read once at startup.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_ENV_FILE = ".env"


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int, *, minimum: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def _get_optional_int(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _get_ids(name: str) -> frozenset[int]:
    """Parse a comma separated list of Discord snowflakes."""
    raw = os.getenv(name, "")
    ids: set[int] = set()
    for part in raw.replace("\n", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError as exc:
            raise ValueError(f"{name} contains a non-integer id: {part!r}") from exc
    return frozenset(ids)


@dataclass(frozen=True, slots=True)
class Config:
    token: str
    command_prefix: str = "!"
    log_level: str = "INFO"
    log_file: Path | None = None
    log_channel_id: int | None = None
    message_cache_size: int = 1000
    max_content_chars: int = 1000
    ignored_channel_ids: frozenset[int] = frozenset()
    ignored_user_ids: frozenset[int] = frozenset()
    log_bot_messages: bool = False
    member_events: bool = True
    owner_id: int | None = None

    @classmethod
    def from_env(cls, env_file: str | Path | None = DEFAULT_ENV_FILE) -> Config:
        """Build a config from environment variables / a dotenv file.

        Real environment variables always win over the .env file, which makes
        container deployments straightforward.
        """
        load_dotenv(env_file, override=False)
        token = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
        if not token:
            raise ValueError(
                "No bot token found. Set DISCORD_TOKEN (or TOKEN) in the "
                "environment or in your .env file."
            )

        log_path = os.getenv("LOG_FILE")
        return cls(
            token=token,
            command_prefix=os.getenv("COMMAND_PREFIX", "!"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_file=Path(log_path).expanduser() if log_path else None,
            log_channel_id=_get_optional_int("LOG_CHANNEL_ID"),
            message_cache_size=_get_int("MESSAGE_CACHE_SIZE", 1000, minimum=1),
            max_content_chars=_get_int("MAX_CONTENT_CHARS", 1000, minimum=50),
            ignored_channel_ids=_get_ids("IGNORED_CHANNEL_IDS"),
            ignored_user_ids=_get_ids("IGNORED_USER_IDS"),
            log_bot_messages=_get_bool("LOG_BOT_MESSAGES", False),
            member_events=_get_bool("ENABLE_MEMBER_EVENTS", True),
            owner_id=_get_optional_int("OWNER_ID"),
        )
