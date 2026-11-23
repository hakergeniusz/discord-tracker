"""Tracking listeners for message and membership events."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from ..config import Config
from ..events import EventLogger, TrackerEvent
from ..message_cache import MessageCache, MessageSnapshot
from ..utils import format_timestamp, truncate

log = logging.getLogger(__name__)

COLOR_SEND = 0x2ECC71
COLOR_EDIT = 0xF1C40F
COLOR_DELETE = 0xE74C3C
COLOR_MEMBER = 0x3498DB
COLOR_GUILD = 0x9B59B6


class Events(commands.Cog):
    """Listen for Discord events and forward normalized records."""

    def __init__(
        self,
        bot: commands.Bot,
        *,
        config: Config,
        cache: MessageCache,
        event_logger: EventLogger,
    ) -> None:
        self.bot = bot
        self.config = config
        self.cache = cache
        self.logger = event_logger

    async def _emit(self, event: TrackerEvent) -> None:
        self.logger.log(event)
        await self.logger.mirror(event)

    def _should_track(self, message: discord.Message) -> bool:
        if self.bot.user is not None and message.author.id == self.bot.user.id:
            return False
        if message.author.bot and not self.config.log_bot_messages:
            return False
        if message.channel.id in self.config.ignored_channel_ids:
            return False
        if message.author.id in self.config.ignored_user_ids:
            return False
        return True

    def _content(self, content: str | None) -> str:
        return truncate(content or "(no content)", self.config.max_content_chars)

    def _fields(self, snapshot: MessageSnapshot, *, content: str | None = None) -> tuple:
        body = self._content(snapshot.content if content is None else content)
        fields: list[tuple[str, str]] = [
            ("Message ID", str(snapshot.id)),
            ("Author", f"{snapshot.author_name} ({snapshot.author_id})"),
            ("Channel", f"<#{snapshot.channel_id}>"),
            ("Created", format_timestamp(snapshot.created_at)),
            ("Content", body),
        ]
        if snapshot.attachments:
            fields.append(("Attachments", ", ".join(snapshot.attachments)))
        return tuple(fields)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if self.bot.user is not None:
            log.info("Logged in as %s (id=%s)", self.bot.user, self.bot.user.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self._should_track(message):
            return
        self.cache.put(message)
        snapshot = MessageCache.snapshot(message)
        await self._emit(
            TrackerEvent(
                action="Message sent",
                fields=self._fields(snapshot),
                color=COLOR_SEND,
                guild_name=getattr(message.guild, "name", None),
            )
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        snapshot = self.cache.remove(payload.message_id)
        if snapshot is None and payload.cached_message is not None:
            snapshot = MessageCache.snapshot(payload.cached_message)

        if snapshot is not None:
            if snapshot.channel_id in self.config.ignored_channel_ids:
                return
            if snapshot.author_id in self.config.ignored_user_ids:
                return
            fields = self._fields(snapshot)
            fields += (("Deleted", format_timestamp(discord.utils.utcnow())),)
        else:
            fields = (
                ("Message ID", str(payload.message_id)),
                ("Content", "Not in cache (content unknown)"),
            )

        await self._emit(
            TrackerEvent(
                action="Message deleted",
                fields=fields,
                color=COLOR_DELETE,
                guild_name=getattr(payload.cached_message.guild, "name", None)
                if payload.cached_message is not None
                else None,
            )
        )

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageEditEvent) -> None:
        data = payload.data
        new_content: str | None = data.get("content") if isinstance(data, dict) else None
        if new_content is None and payload.cached_message is not None:
            new_content = payload.cached_message.content

        previous = self.cache.get(payload.message_id)
        if previous is None or new_content is None:
            return
        if previous.content == new_content:
            return  # embed/pin update, not a content change

        self.cache.mark_edited(payload.message_id, new_content)
        fields = (
            ("Message ID", str(payload.message_id)),
            ("Author", f"{previous.author_name} ({previous.author_id})"),
            ("Channel", f"<#{previous.channel_id}>"),
            ("Before", self._content(previous.content)),
            ("After", self._content(new_content)),
            ("Edited", format_timestamp(discord.utils.utcnow())),
        )
        await self._emit(
            TrackerEvent(
                action="Message edited",
                fields=fields,
                color=COLOR_EDIT,
                guild_name=getattr(payload.cached_message.guild, "name", None)
                if payload.cached_message is not None
                else None,
            )
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self._emit(
            TrackerEvent(
                action="Member joined",
                fields=(
                    ("Member", f"{member} ({member.id})"),
                    ("Account created", format_timestamp(member.created_at)),
                ),
                color=COLOR_MEMBER,
                guild_name=member.guild.name,
            )
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        await self._emit(
            TrackerEvent(
                action="Member left",
                fields=(("Member", f"{member} ({member.id})"),),
                color=COLOR_MEMBER,
                guild_name=member.guild.name,
            )
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        log.info("Joined guild %s (id=%s)", guild.name, guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        log.info("Left guild %s (id=%s)", guild.name, guild.id)
