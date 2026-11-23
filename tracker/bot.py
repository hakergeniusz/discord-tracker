"""The bot class and its startup wiring."""

from __future__ import annotations

import asyncio
import logging
import signal
from datetime import UTC, datetime

import discord
from discord.ext import commands

from .cogs.events import Events
from .cogs.utility import Utility
from .config import Config
from .events import EventLogger
from .message_cache import MessageCache

log = logging.getLogger(__name__)


class TrackerBot(commands.Bot):
    """Discord bot wired up with the tracker's cogs and shared state."""

    def __init__(self, config: Config) -> None:
        self.config = config
        # Least privilege: no presences, reactions, voice, typing, etc.
        intents = discord.Intents(
            guilds=True,
            members=config.member_events,
            messages=True,
            message_content=True,
        )
        super().__init__(
            command_prefix=config.command_prefix,
            intents=intents,
            help_command=None,
        )
        if config.owner_id is not None:
            self.owner_id = config.owner_id

        self.cache = MessageCache(config.message_cache_size)
        self.event_logger = EventLogger(self, config)
        self.started_at = datetime.now(UTC)

    async def setup_hook(self) -> None:
        await self.add_cog(
            Events(self, config=self.config, cache=self.cache, event_logger=self.event_logger)
        )
        await self.add_cog(
            Utility(self, event_logger=self.event_logger, started_at=self.started_at)
        )
        log.info("Cogs loaded: %s", ", ".join(sorted(self.cogs)))

        # discord.py handles Ctrl-C already; SIGTERM (docker, systemd) needs a hand.
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(self.close()))
        except NotImplementedError:  # not available on every platform
            pass

    async def close(self) -> None:
        log.info("Shutting down cleanly...")
        await super().close()
