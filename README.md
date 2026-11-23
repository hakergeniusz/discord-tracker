# discord-tracker

A Discord bot that watches messages and membership changes, keeps a short
memory of recent messages so deleted/edited content can still be reported, and
mirrors events to a channel of your choosing.

## Features

- Structured logging to the console and an optional rotating log file.
- Optional mirroring of tracked events to a Discord channel as embeds.
- Bounded LRU message cache: deleted and edited messages keep their original
  content even after Discord drops them from its own cache.
- Least-privilege intents (guilds, members, messages, message content only).
- Cog based structure, hybrid prefix/slash commands, and graceful shutdown on
  SIGTERM.

## Tracked events

- Message sent, edited, and deleted (including bulk deletions).
- Member joined / left.
- Bot joined / left a guild.

Channels, users, and bot messages can be excluded via configuration.

## Setup

```sh
uv sync
cp .env.example .env   # then fill in DISCORD_TOKEN
uv run python main.py
```

Enable the **Message Content Intent** for your application in the Discord
developer portal, then invite the bot with the `bot` scope and permissions to
read and send messages.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DISCORD_TOKEN` | required | Bot token (`TOKEN` is accepted too). |
| `COMMAND_PREFIX` | `!` | Prefix for text commands. |
| `LOG_LEVEL` | `INFO` | Root logging level. |
| `LOG_FILE` | unset | Write logs to a rotating file at this path. |
| `LOG_CHANNEL_ID` | unset | Mirror events to this channel ID. |
| `MESSAGE_CACHE_SIZE` | `1000` | How many recent messages to remember. |
| `MAX_CONTENT_CHARS` | `1000` | Truncate logged message content to this length. |
| `IGNORED_CHANNEL_IDS` | empty | Comma separated channel IDs to skip. |
| `IGNORED_USER_IDS` | empty | Comma separated user IDs to skip. |
| `LOG_BOT_MESSAGES` | `false` | Whether to track other bots' messages. |
| `ENABLE_MEMBER_EVENTS` | `true` | Track joins/leaves (needs the Server Members Intent). |
| `OWNER_ID` | unset | Bot owner, allowed to run `!sync`. |

If you have not enabled the Server Members Intent in the developer portal, set
`ENABLE_MEMBER_EVENTS=false`; the bot will then not request that intent.

## Commands

| Command | Description |
| --- | --- |
| `ping` | Show gateway latency. |
| `uptime` | Show how long the bot has been running. |
| `stats` | Show guild count, events logged, and cache usage. |
| `setlogchannel [#channel]` | Set the mirror channel, or omit it to disable (requires Manage Server). |
| `sync` | Sync slash commands (owner only). |

## Development

```sh
uv run ruff check .
uv run pytest
```
