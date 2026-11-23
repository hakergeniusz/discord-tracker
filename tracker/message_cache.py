"""A bounded in-memory snapshot of recently seen messages.

Discord only hands us the content of a deleted message while it is still in
the gateway cache (typically a few minutes). Keeping our own small LRU cache
means we can still report what was removed, and what a message said before it
was edited, long after Discord has forgotten about it.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class MessageSnapshot:
    id: int
    channel_id: int
    guild_id: int | None
    author_id: int
    author_name: str
    content: str
    created_at: datetime
    attachments: tuple[str, ...] = ()
    edits: int = 0


class MessageCache:
    """Least-recently-used cache keyed by message id."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._entries: OrderedDict[int, MessageSnapshot] = OrderedDict()

    @staticmethod
    def snapshot(message) -> MessageSnapshot:
        """Create an immutable snapshot from a discord.py message-like object."""
        created = message.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        return MessageSnapshot(
            id=message.id,
            channel_id=message.channel.id,
            guild_id=getattr(message.guild, "id", None),
            author_id=message.author.id,
            author_name=str(message.author),
            content=message.content or "",
            created_at=created.astimezone(UTC),
            attachments=tuple(attachment.filename for attachment in message.attachments),
        )

    def put(self, message) -> None:
        snapshot = self.snapshot(message)
        self._entries[snapshot.id] = snapshot
        self._entries.move_to_end(snapshot.id)
        if len(self._entries) > self.capacity:
            self._entries.popitem(last=False)

    def get(self, message_id: int) -> MessageSnapshot | None:
        snapshot = self._entries.get(message_id)
        if snapshot is not None:
            self._entries.move_to_end(message_id)
        return snapshot

    def remove(self, message_id: int) -> MessageSnapshot | None:
        return self._entries.pop(message_id, None)

    def mark_edited(self, message_id: int, new_content: str) -> MessageSnapshot | None:
        """Record a new content value and return the previous snapshot."""
        previous = self.get(message_id)
        if previous is None:
            return None
        updated = replace(previous, content=new_content, edits=previous.edits + 1)
        self._entries[message_id] = updated
        self._entries.move_to_end(message_id)
        return previous

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
