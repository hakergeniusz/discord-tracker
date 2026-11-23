"""Utility and management commands."""

from __future__ import annotations

import logging
from datetime import datetime

import discord
from discord.ext import commands

from .. import __version__
from ..events import EventLogger
from ..utils import format_duration, utcnow

log = logging.getLogger(__name__)


class Utility(commands.Cog):
    """Small commands for inspecting and managing the tracker."""

    def __init__(
        self,
        bot: commands.Bot,
        *,
        event_logger: EventLogger,
        started_at: datetime,
    ) -> None:
        self.bot = bot
        self.logger = event_logger
        self.started_at = started_at

    @commands.hybrid_command(name="ping", description="Check the bot's latency.")
    async def ping(self, ctx: commands.Context) -> None:
        latency = self.bot.latency
        ms = "unknown" if latency != latency else f"{latency * 1000:.0f} ms"
        await ctx.send(f"Pong! {ms}")

    @commands.hybrid_command(name="uptime", description="Show how long the bot has been up.")
    async def uptime(self, ctx: commands.Context) -> None:
        await ctx.send(f"Uptime: {format_duration((utcnow() - self.started_at).total_seconds())}")

    @commands.hybrid_command(name="stats", description="Show tracker statistics.")
    async def stats(self, ctx: commands.Context) -> None:
        lines = [
            f"Version: {__version__}",
            f"Guilds: {len(self.bot.guilds)}",
            f"Events logged this session: {self.logger.event_count}",
            f"Cached messages: {len(self.bot.cache)}/{self.bot.cache.capacity}",
            f"Log channel: {self.logger.channel_id or 'disabled'}",
        ]
        await ctx.send("\n".join(lines))

    @commands.command(name="setlogchannel")
    @commands.has_permissions(manage_guild=True)
    async def setlogchannel(
        self, ctx: commands.Context, channel: discord.TextChannel | None = None
    ) -> None:
        """Set the channel events are mirrored to, or omit it to disable."""
        if channel is None:
            self.logger.set_channel(None)
            await ctx.send("Event mirroring disabled.")
            return
        self.logger.set_channel(channel.id)
        await ctx.send(f"Event mirroring set to {channel.mention}.")

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context) -> None:
        """Sync slash commands with Discord (owner only)."""
        commands_synced = await self.bot.tree.sync()
        await ctx.send(f"Synced {len(commands_synced)} slash command(s).")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.NotOwner):
            await ctx.send("You are not allowed to use that command.")
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You lack the permissions required for that command.")
            return
        log.error("Command %r failed: %s", ctx.command, error, exc_info=error)
        await ctx.send("Something went wrong while running that command.")

    @commands.Cog.listener()
    async def on_app_command_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        log.error("App command %r failed: %s", interaction.command, error, exc_info=error)
        message = "Something went wrong while running that command."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
