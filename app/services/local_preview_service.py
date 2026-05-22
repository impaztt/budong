from __future__ import annotations

from typing import Any

from app.crawlers.base_crawler import BaseCrawler
from app.crawlers.crawler_factory import create_crawler
from app.crawlers.exceptions import CrawlerError
from app.repositories.local_json_repository import LocalJsonRepository
from app.services.url_resolver_service import UrlResolverService
from app.utils.date_utils import utc_now_iso


class LocalPreviewService:
    def __init__(
        self,
        repository: LocalJsonRepository | None = None,
        resolver: UrlResolverService | None = None,
    ) -> None:
        self.repository = repository or LocalJsonRepository()
        self.resolver = resolver or UrlResolverService()

    def list_sources(self) -> list[dict[str, Any]]:
        return self.repository.list_sources()

    def list_listings(self, source_id: int | None = None) -> list[dict[str, Any]]:
        return self.repository.list_listings(source_id=source_id)

    def crawl_url(self, source_url: str, memo: str | None = None) -> dict[str, Any]:
        resolved = self.resolver.resolve(source_url)
        source = self.repository.upsert_source(
            source_url=resolved.source_url,
            resolved_url=resolved.resolved_url,
            source_type=resolved.source_type,
            memo=memo,
            status="RUNNING",
        )
        self.repository.update_source(
            source["id"],
            {"last_crawled_at": utc_now_iso(), "last_error_message": None},
        )

        crawler: BaseCrawler | None = None
        try:
            crawler = create_crawler(source.get("source_type") or "UNKNOWN")
            result = crawler.crawl(source)
            collected_at = utc_now_iso()
            listings = [
                {
                    **listing,
                    "source_url_id": source["id"],
                    "source_url": listing.get("source_url")
                    or source.get("resolved_url")
                    or source.get("source_url"),
                    "last_seen_at": collected_at,
                    "is_active": True,
                }
                for listing in result.listings
            ]
            self.repository.upsert_listings(source["id"], listings)
            self.repository.append_logs(source["id"], result.request_logs)
            self.repository.update_source(
                source["id"],
                {
                    "crawl_status": "SUCCESS",
                    "last_success_at": collected_at,
                    "last_error_message": None,
                    "last_count": len(listings),
                },
            )
            return {
                "source": self.repository.update_source(
                    source["id"],
                    {"last_count": len(listings)},
                ),
                "total_count": len(listings),
                "listings": listings,
                "request_logs": result.request_logs,
                "raw_length": result.raw_length,
                "raw_preview": result.raw_preview,
                "parser_message": result.parser_message,
            }
        except CrawlerError as exc:
            logs = crawler.request_logs if crawler is not None else []
            if logs:
                self.repository.append_logs(source["id"], logs)
            error_type = getattr(exc, "error_type", "CRAWLER_ERROR")
            status = self._status_for_error(error_type)
            failed_source = self.repository.update_source(
                source["id"],
                {
                    "crawl_status": status,
                    "last_failed_at": utc_now_iso(),
                    "last_error_message": str(exc),
                },
            )
            return {
                "source": failed_source,
                "total_count": 0,
                "listings": [],
                "request_logs": logs,
                "error_type": error_type,
                "error_message": str(exc),
            }

    def _status_for_error(self, error_type: str) -> str:
        if error_type == "HTTP_429_TOO_MANY_REQUESTS":
            return "RATE_LIMITED"
        if error_type == "HTTP_403_FORBIDDEN":
            return "BLOCKED"
        if error_type == "UNSUPPORTED_SOURCE":
            return "UNSUPPORTED"
        return "FAILED"
