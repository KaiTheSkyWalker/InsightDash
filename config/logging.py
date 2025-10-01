from loguru import logger


def configure_logging():
    """Configure a single stderr sink with a unified format and per-tab file sinks.

    Tabs can log via `logger.bind(tab="Tab1")` etc so the sink prints a clear prefix.
    """
    # Remove all sinks; no logging per request
    logger.remove()
    logger.configure(extra={"tab": "App"})
    # If you later want minimal stderr logs, reintroduce `import sys` above and uncomment below:
    # logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[tab]}] {message}", level="WARNING")
    logger.add("logs/usage.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO", filter=lambda record: "usage" in record["extra"])
