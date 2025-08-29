import sys
from loguru import logger


def configure_logging():
    """Configure a single stderr sink with a unified format and per-tab file sinks.

    Tabs can log via `logger.bind(tab="Tab1")` etc so the sink prints a clear prefix.
    """
    # Reset and configure a single console sink
    logger.remove()
    logger.configure(extra={"tab": "App"})
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[tab]}] {message}",
        level="INFO",
    )

    # Optional: per-tab file sinks when using extra.tab values
    logger.add(
        "logs/tab1_results_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        level="INFO",
        filter=lambda r: r["extra"].get("tab") == "Tab1",
    )
    logger.add(
        "logs/tab2_results_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        level="INFO",
        filter=lambda r: r["extra"].get("tab") == "Tab2",
    )
    # Tab3 mostly logs UI events; keep console only. Add a file sink if desired.

