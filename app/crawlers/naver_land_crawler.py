from __future__ import annotations

import time
from typing import Any

from app.config.settings import settings
from app.crawlers.base_crawler import BaseCrawler, CrawlResult
from app.crawlers.exceptions import CrawlRequestError
from app.parsers.naver_land_parser import NaverLandParser


class NaverLandCrawler(BaseCrawler):
    def __init__(self) -> None:
        super().__init__()
        self.parser = NaverLandParser()

    def crawl(self, source: dict[str, Any]) -> CrawlResult:
        source_url_id = source.get("id")
        target_url = source.get("resolved_url") or source.get("source_url")
        if not target_url:
            raise CrawlRequestError("No source URL is available.")

        started = time.monotonic()
        response = self.fetch(target_url)
        if time.monotonic() - started > settings.crawl_max_seconds_per_url:
            raise CrawlRequestError("Maximum crawl runtime exceeded.")

        listings = self.parser.parse(response.text, source_url=target_url)
        limited_listings = listings[: settings.crawl_max_listings_per_url]
        return CrawlResult(
            source_url_id=source_url_id,
            source_type="NAVER_LAND",
            listings=limited_listings,
            request_logs=self.request_logs,
        )
