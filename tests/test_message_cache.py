from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from tracker.message_cache import MessageCache


@dataclass
class FakeAuthor:
    id: int
    name: str

    def __str__(self):
        return self.name


@dataclass
class FakeChannel:
    id: int


@dataclass
class FakeGuild:
    id: int


@dataclass
class FakeAttachment:
    filename: str


@dataclass
class FakeMessage:
    id: int
    channel: FakeChannel
    author: FakeAuthor
    content: str
    created_at: datetime
    guild: FakeGuild | None = None
    attachments: tuple = ()


def make_message(message_id: int, content: str = "hello") -> FakeMessage:
    return FakeMessage(
        id=message_id,
        channel=FakeChannel(10),
        author=FakeAuthor(7, "tester"),
        content=content,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        guild=FakeGuild(5),
        attachments=(FakeAttachment("pic.png"),),
    )


def test_snapshot_extracts_fields():
    snapshot = MessageCache.snapshot(make_message(1))
    assert snapshot.id == 1
    assert snapshot.channel_id == 10
    assert snapshot.guild_id == 5
    assert snapshot.author_id == 7
    assert snapshot.author_name == "tester"
    assert snapshot.content == "hello"
    assert snapshot.attachments == ("pic.png",)


def test_put_get_and_remove():
    cache = MessageCache(3)
    cache.put(make_message(1))
    assert len(cache) == 1
    assert cache.get(1).content == "hello"
    assert cache.remove(1).id == 1
    assert cache.get(1) is None


def test_lru_eviction():
    cache = MessageCache(2)
    cache.put(make_message(1, "one"))
    cache.put(make_message(2, "two"))
    cache.get(1)  # refresh -> 2 becomes least recently used
    cache.put(make_message(3, "three"))
    assert cache.get(1) is not None
    assert cache.get(2) is None
    assert cache.get(3) is not None
    assert len(cache) == 2


def test_mark_edited_returns_previous():
    cache = MessageCache(5)
    cache.put(make_message(1, "before"))
    previous = cache.mark_edited(1, "after")
    assert previous is not None
    assert previous.content == "before"
    assert cache.get(1).content == "after"
    assert cache.get(1).edits == 1
    assert cache.mark_edited(999, "nope") is None


def test_capacity_validation():
    with pytest.raises(ValueError):
        MessageCache(0)


def test_clear():
    cache = MessageCache(5)
    cache.put(make_message(1))
    cache.clear()
    assert len(cache) == 0
