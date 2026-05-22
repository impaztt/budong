from __future__ import annotations

import sys

from loguru import logger

from app.config.settings import settings


def configure_logging() -> None:
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    logger.add(
        settings.log_dir / "app.log",
        level=settings.log_level,
        rotation="10 MB",
        retention="14 days",
        encoding="utf-8",
    )
    logger.add(
        settings.log_dir / "crawl_{time:YYYYMMDD}.log",
        level=settings.log_level,
        rotation="1 day",
        retention="30 days",
        encoding="utf-8",
        filter=lambda record: record["extra"].get("category") == "crawl",
    )
