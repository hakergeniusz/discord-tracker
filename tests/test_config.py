import pytest

from tracker.config import Config

ENV_KEYS = (
    "DISCORD_TOKEN",
    "TOKEN",
    "COMMAND_PREFIX",
    "LOG_LEVEL",
    "LOG_FILE",
    "LOG_CHANNEL_ID",
    "MESSAGE_CACHE_SIZE",
    "MAX_CONTENT_CHARS",
    "IGNORED_CHANNEL_IDS",
    "IGNORED_USER_IDS",
    "LOG_BOT_MESSAGES",
    "ENABLE_MEMBER_EVENTS",
    "OWNER_ID",
)
MISSING_ENV = "/definitely/not/a/real/.env"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_missing_token_raises():
    with pytest.raises(ValueError, match="No bot token"):
        Config.from_env(env_file=MISSING_ENV)


def test_defaults(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "abc123")
    config = Config.from_env(env_file=MISSING_ENV)
    assert config.token == "abc123"
    assert config.command_prefix == "!"
    assert config.log_level == "INFO"
    assert config.log_file is None
    assert config.log_channel_id is None
    assert config.message_cache_size == 1000
    assert config.ignored_channel_ids == frozenset()
    assert config.log_bot_messages is False
    assert config.member_events is True


def test_parses_values(monkeypatch):
    monkeypatch.setenv("TOKEN", "fallback-token")
    monkeypatch.setenv("COMMAND_PREFIX", "?")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("LOG_CHANNEL_ID", "12345")
    monkeypatch.setenv("MESSAGE_CACHE_SIZE", "25")
    monkeypatch.setenv("MAX_CONTENT_CHARS", "250")
    monkeypatch.setenv("IGNORED_CHANNEL_IDS", "1, 2\n3")
    monkeypatch.setenv("IGNORED_USER_IDS", "42")
    monkeypatch.setenv("LOG_BOT_MESSAGES", "yes")
    monkeypatch.setenv("ENABLE_MEMBER_EVENTS", "false")
    monkeypatch.setenv("OWNER_ID", "99")

    config = Config.from_env(env_file=MISSING_ENV)
    assert config.command_prefix == "?"
    assert config.log_level == "DEBUG"
    assert config.log_channel_id == 12345
    assert config.message_cache_size == 25
    assert config.max_content_chars == 250
    assert config.ignored_channel_ids == frozenset({1, 2, 3})
    assert config.ignored_user_ids == frozenset({42})
    assert config.log_bot_messages is True
    assert config.member_events is False
    assert config.owner_id == 99


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("MESSAGE_CACHE_SIZE", "0"),
        ("MESSAGE_CACHE_SIZE", "abc"),
        ("LOG_CHANNEL_ID", "abc"),
        ("MAX_CONTENT_CHARS", "nope"),
        ("IGNORED_USER_IDS", "1,oops"),
    ],
)
def test_invalid_values_raise(monkeypatch, key, value):
    monkeypatch.setenv("DISCORD_TOKEN", "abc")
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        Config.from_env(env_file=MISSING_ENV)
