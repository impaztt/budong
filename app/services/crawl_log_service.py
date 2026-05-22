from __future__ import annotations

from typing import Any

from app.repositories.crawl_log_repository import CrawlLogRepository


class CrawlLogService:
    def __init__(self, repository: CrawlLogRepository | None = None) -> None:
        self.repository = repository or CrawlLogRepository()

    def save_request_logs(
        self,
        crawl_job_id: int,
        source_url_id: int | None,
        logs: list[dict[str, Any]],
    ) -> None:
        payloads = [
            {
                **log,
                "crawl_job_id": crawl_job_id,
                "source_url_id": source_url_id,
            }
            for log in logs
        ]
        self.repository.create_many(payloads)
