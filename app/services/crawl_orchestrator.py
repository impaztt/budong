from __future__ import annotations

from typing import Any

from loguru import logger

from app.crawlers.base_crawler import BaseCrawler
from app.crawlers.crawler_factory import create_crawler
from app.crawlers.exceptions import CrawlerError
from app.services.crawl_job_service import CrawlJobService
from app.services.crawl_log_service import CrawlLogService
from app.services.listing_service import ListingService
from app.services.source_url_service import SourceUrlService
from app.utils.date_utils import utc_now_iso


class CrawlOrchestrator:
    def __init__(
        self,
        source_url_service: SourceUrlService | None = None,
        crawl_job_service: CrawlJobService | None = None,
        listing_service: ListingService | None = None,
        crawl_log_service: CrawlLogService | None = None,
    ) -> None:
        self.source_url_service = source_url_service or SourceUrlService()
        self.crawl_job_service = crawl_job_service or CrawlJobService()
        self.listing_service = listing_service or ListingService()
        self.crawl_log_service = crawl_log_service or CrawlLogService()

    def crawl_source(self, source_id: int) -> dict[str, Any]:
        source = self.source_url_service.get_source_url(source_id)
        job = self.crawl_job_service.create_job(source_id)
        job_id = job["id"]
        self.crawl_job_service.mark_running(job_id)
        self.source_url_service.repository.update(
            source_id,
            {"crawl_status": "RUNNING", "last_crawled_at": utc_now_iso()},
        )

        crawler: BaseCrawler | None = None
        logs_saved = False
        try:
            crawler = create_crawler(source.get("source_type") or "UNKNOWN")
            result = crawler.crawl(source)
            self._save_logs_safely(
                crawl_job_id=job_id,
                source_url_id=source.get("id"),
                logs=result.request_logs,
            )
            logs_saved = True
            counts = self.listing_service.save_listings(
                source=source,
                crawl_job_id=job_id,
                listings=result.listings,
            )
            self.crawl_job_service.mark_success(job_id, **counts)
            self.source_url_service.repository.update(
                source_id,
                {
                    "crawl_status": "SUCCESS",
                    "last_success_at": utc_now_iso(),
                    "last_error_message": None,
                },
            )
            return {"source_id": source_id, "job_id": job_id, **counts}
        except CrawlerError as exc:
            if crawler is not None and not logs_saved:
                self._save_logs_safely(
                    crawl_job_id=job_id,
                    source_url_id=source.get("id"),
                    logs=crawler.request_logs,
                )
            error_type = getattr(exc, "error_type", "CRAWLER_ERROR")
            status = "RATE_LIMITED" if error_type == "HTTP_429_TOO_MANY_REQUESTS" else "FAILED"
            if error_type == "HTTP_403_FORBIDDEN":
                status = "BLOCKED"
            if error_type == "UNSUPPORTED_SOURCE":
                status = "UNSUPPORTED"
            self.crawl_job_service.mark_failed(job_id, error_type, str(exc))
            self.source_url_service.repository.update(
                source_id,
                {
                    "crawl_status": status,
                    "last_failed_at": utc_now_iso(),
                    "last_error_message": str(exc),
                },
            )
            logger.exception("crawl failed source_id={} error_type={}", source_id, error_type)
            return {
                "source_id": source_id,
                "job_id": job_id,
                "total_count": 0,
                "success_count": 0,
                "failed_count": 1,
                "error_type": error_type,
                "error_message": str(exc),
            }
        except Exception as exc:
            if crawler is not None and not logs_saved:
                self._save_logs_safely(
                    crawl_job_id=job_id,
                    source_url_id=source.get("id"),
                    logs=crawler.request_logs,
                )
            error_type = "UNEXPECTED_ERROR"
            self.crawl_job_service.mark_failed(job_id, error_type, str(exc))
            self.source_url_service.repository.update(
                source_id,
                {
                    "crawl_status": "FAILED",
                    "last_failed_at": utc_now_iso(),
                    "last_error_message": str(exc),
                },
            )
            logger.exception("crawl failed source_id={} error_type={}", source_id, error_type)
            return {
                "source_id": source_id,
                "job_id": job_id,
                "total_count": 0,
                "success_count": 0,
                "failed_count": 1,
                "error_type": error_type,
                "error_message": str(exc),
            }

    def crawl_url(self, source_url: str, memo: str | None = None) -> dict[str, Any]:
        source = self.source_url_service.register_url(source_url, memo=memo)
        return self.crawl_source(source["id"])

    def crawl_active(self) -> list[dict[str, Any]]:
        sources = self.source_url_service.list_source_urls(active_only=True)
        return [self.crawl_source(source["id"]) for source in sources]

    def crawl_pending(self) -> list[dict[str, Any]]:
        sources = self.source_url_service.list_source_urls(
            active_only=True,
            status="PENDING",
        )
        return [self.crawl_source(source["id"]) for source in sources]

    def _save_logs_safely(
        self,
        crawl_job_id: int,
        source_url_id: int | None,
        logs: list[dict[str, Any]],
    ) -> None:
        try:
            self.crawl_log_service.save_request_logs(crawl_job_id, source_url_id, logs)
        except Exception as exc:
            logger.warning("failed to save crawl logs: {}", exc)
