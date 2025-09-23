from loguru import logger
import sys


def configure_logging():
    """Configure a single stderr sink with a unified format and per-tab file sinks.

    Tabs can log via `logger.bind(tab="Tab1")` etc so the sink prints a clear prefix.
    """
    # Remove all sinks; no logging per request
    logger.remove()
    logger.configure(extra={"tab": "App"})
    # If you later want minimal stderr logs, uncomment below and set level:
    # logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[tab]}] {message}", level="WARNING")
    logger.add("logs/usage.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO", filter=lambda record: "usage" in record["extra"])
