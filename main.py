"""Entry point for the Discord tracker bot."""

from __future__ import annotations

import logging
import sys

from tracker.bot import TrackerBot
from tracker.config import Config
from tracker.logging_config import setup_logging

log = logging.getLogger(__name__)


def main() -> None:
    try:
        config = Config.from_env()
        setup_logging(config)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    bot = TrackerBot(config)
    try:
        # Logging is configured above, so disable discord.py's own handler.
        bot.run(config.token, log_handler=None)
    except KeyboardInterrupt:
        log.info("Interrupted by user.")
    finally:
        log.info("Bot stopped.")


if __name__ == "__main__":
    main()
