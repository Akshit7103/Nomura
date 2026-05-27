"""Logging setup. Stdlib logging, UTF-8 safe for Windows consoles."""

import logging
import sys
from datetime import datetime
from pathlib import Path

_CONFIGURED = False


def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> None:
    """Configure root logging once: clean console + rotating-by-day file."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    # Avoid cp1252 crashes when logging em-dashes / emojis on Windows.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"email_agent_{datetime.now():%Y%m%d}.log"

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)-22s | %(message)s",
        datefmt="%H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file_handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
