from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


@dataclass(frozen=True)
class Settings:
    supabase_url: str | None
    supabase_key: str | None
    crawl_delay_seconds: float
    crawl_timeout_seconds: int
    crawl_max_retry: int
    crawl_max_listings_per_url: int
    crawl_max_pages_per_url: int
    crawl_max_seconds_per_url: int
    export_dir: Path
    log_dir: Path
    local_data_dir: Path
    log_level: str

    @property
    def has_supabase_credentials(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)


def get_settings() -> Settings:
    return Settings(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        crawl_delay_seconds=_get_float("CRAWL_DELAY_SECONDS", 1.0),
        crawl_timeout_seconds=_get_int("CRAWL_TIMEOUT_SECONDS", 15),
        crawl_max_retry=_get_int("CRAWL_MAX_RETRY", 2),
        crawl_max_listings_per_url=_get_int("CRAWL_MAX_LISTINGS_PER_URL", 500),
        crawl_max_pages_per_url=_get_int("CRAWL_MAX_PAGES_PER_URL", 10),
        crawl_max_seconds_per_url=_get_int("CRAWL_MAX_SECONDS_PER_URL", 600),
        export_dir=Path(os.getenv("EXPORT_DIR", "./exports")),
        log_dir=Path(os.getenv("LOG_DIR", "./logs")),
        local_data_dir=Path(os.getenv("LOCAL_DATA_DIR", "./data")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = get_settings()
