"""Behaviour tests for the tracking listeners, without a live Discord connection."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace

from tracker.cogs.events import Events
from tracker.config import Config
from tracker.message_cache import MessageCache


@dataclass
class FakeAuthor:
    id: int
    name: str
    bot: bool = False

    def __str__(self):
        return self.name


@dataclass
class FakeChannel:
    id: int


@dataclass
class FakeGuild:
    id: int
    name: str


def make_message(message_id, content, *, author_id=7, channel_id=10, bot=False):
    guild = FakeGuild(5, "Test Guild")
    return SimpleNamespace(
        id=message_id,
        channel=FakeChannel(channel_id),
        guild=guild,
        author=FakeAuthor(author_id, "tester", bot),
        content=content,
        created_at=datetime(2026, 1, 1),
        attachments=(),
    )


class RecordingLogger:
    def __init__(self):
        self.events = []

    def log(self, event):
        self.events.append(event)

    async def mirror(self, event):
        return None


def build_cog(config=None):
    config = config or Config(token="dummy", message_cache_size=10)
    cache = MessageCache(config.message_cache_size)
    logger = RecordingLogger()
    bot = SimpleNamespace(user=FakeAuthor(999, "tracker"))
    cog = Events(bot, config=config, cache=cache, event_logger=logger)
    return cog, cache, logger


def run(coro):
    return asyncio.run(coro)


def test_message_sent_is_cached_and_emitted():
    cog, cache, logger = build_cog()
    run(cog.on_message(make_message(1, "hello")))
    assert cache.get(1).content == "hello"
    assert [e.action for e in logger.events] == ["Message sent"]


def test_bot_and_ignored_messages_are_skipped():
    cog, _, logger = build_cog(Config(token="x", ignored_channel_ids=frozenset({10})))
    run(cog.on_message(make_message(1, "hi")))
    assert logger.events == []

    cog, _, logger = build_cog(Config(token="x", ignored_user_ids=frozenset({7})))
    run(cog.on_message(make_message(2, "hi")))
    assert logger.events == []

    cog, _, logger = build_cog(Config(token="x"))
    run(cog.on_message(make_message(3, "hi", bot=True)))
    assert logger.events == []


def test_delete_uses_cached_content():
    cog, _, logger = build_cog()
    run(cog.on_message(make_message(1, "secret")))
    logger.events.clear()
    payload = SimpleNamespace(message_id=1, cached_message=None)
    run(cog.on_raw_message_delete(payload))
    assert logger.events[0].action == "Message deleted"
    values = dict(logger.events[0].fields)
    assert values["Content"] == "secret"


def test_delete_of_unknown_message_is_reported():
    cog, _, logger = build_cog()
    payload = SimpleNamespace(message_id=55, cached_message=None)
    run(cog.on_raw_message_delete(payload))
    assert "unknown" in dict(logger.events[0].fields)["Content"]


def test_edit_reports_before_and_after():
    cog, cache, logger = build_cog()
    run(cog.on_message(make_message(1, "before")))
    logger.events.clear()
    payload = SimpleNamespace(message_id=1, cached_message=None, data={"content": "after"})
    run(cog.on_raw_message_edit(payload))
    assert logger.events[0].action == "Message edited"
    fields = dict(logger.events[0].fields)
    assert fields["Before"] == "before"
    assert fields["After"] == "after"
    assert cache.get(1).content == "after"


def test_edit_without_content_change_is_ignored():
    cog, _, logger = build_cog()
    run(cog.on_message(make_message(1, "same")))
    logger.events.clear()
    payload = SimpleNamespace(message_id=1, cached_message=None, data={"embeds": []})
    run(cog.on_raw_message_edit(payload))
    assert logger.events == []

    payload = SimpleNamespace(message_id=1, cached_message=None, data={"content": "same"})
    run(cog.on_raw_message_edit(payload))
    assert logger.events == []
