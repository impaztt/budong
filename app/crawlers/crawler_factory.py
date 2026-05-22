from __future__ import annotations

from app.crawlers.base_crawler import BaseCrawler
from app.crawlers.exceptions import UnsupportedCrawlerError
from app.crawlers.naver_land_crawler import NaverLandCrawler


def create_crawler(source_type: str) -> BaseCrawler:
    if source_type == "NAVER_LAND":
        return NaverLandCrawler()
    raise UnsupportedCrawlerError(f"Unsupported source type: {source_type}")
