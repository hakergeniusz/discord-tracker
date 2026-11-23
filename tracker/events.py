"""Event representation and dual console/Discord logging."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import discord
from discord.ext import commands

from .config import Config
from .utils import truncate

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TrackerEvent:
    """A single normalized event ready to be rendered anywhere."""

    action: str
    fields: tuple[tuple[str, str], ...]
    color: int
    guild_name: str | None = None

    def as_text(self) -> str:
        lines = [f"[{self.action}]"]
        lines.extend(f"  {name}: {value}" for name, value in self.fields)
        if self.guild_name:
            lines.append(f"  Guild: {self.guild_name}")
        return "\n".join(lines)


class EventLogger:
    """Logs events to the console and, optionally, to a Discord channel."""

    def __init__(self, bot: commands.Bot, config: Config) -> None:
        self.bot = bot
        self.config = config
        self._channel_id = config.log_channel_id
        self.event_count = 0

    def set_channel(self, channel_id: int | None) -> None:
        self._channel_id = channel_id

    @property
    def channel_id(self) -> int | None:
        return self._channel_id

    def log(self, event: TrackerEvent) -> None:
        self.event_count += 1
        log.info("%s", event.as_text())

    async def mirror(self, event: TrackerEvent) -> None:
        """Send an embed to the configured log channel, if any."""
        if self._channel_id is None:
            return

        channel = self.bot.get_channel(self._channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(self._channel_id)
            except (discord.HTTPException, discord.Forbidden, discord.NotFound) as exc:
                log.warning("Could not fetch log channel %s: %s", self._channel_id, exc)
                return

        embed = discord.Embed(title=event.action, color=discord.Color(event.color))
        for name, value in event.fields:
            embed.add_field(name=name, value=truncate(value, 1024), inline=False)
        if event.guild_name:
            embed.set_footer(text=event.guild_name)
        embed.timestamp = discord.utils.utcnow()

        try:
            await channel.send(embed=embed)
        except discord.HTTPException as exc:
            log.warning("Could not send log event to channel %s: %s", self._channel_id, exc)
