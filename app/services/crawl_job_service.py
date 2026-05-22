from __future__ import annotations

from typing import Any

from app.repositories.crawl_job_repository import CrawlJobRepository
from app.utils.date_utils import utc_now_iso


class CrawlJobService:
    def __init__(self, repository: CrawlJobRepository | None = None) -> None:
        self.repository = repository or CrawlJobRepository()

    def create_job(self, source_url_id: int) -> dict[str, Any]:
        return self.repository.create(
            {"source_url_id": source_url_id, "job_status": "READY"}
        )

    def mark_running(self, job_id: int) -> dict[str, Any]:
        return self.repository.update(
            job_id,
            {"job_status": "RUNNING", "started_at": utc_now_iso()},
        )

    def mark_success(
        self,
        job_id: int,
        total_count: int,
        success_count: int,
        failed_count: int = 0,
    ) -> dict[str, Any]:
        status = "SUCCESS" if failed_count == 0 else "PARTIAL_SUCCESS"
        return self.repository.update(
            job_id,
            {
                "job_status": status,
                "finished_at": utc_now_iso(),
                "total_count": total_count,
                "success_count": success_count,
                "failed_count": failed_count,
            },
        )

    def mark_failed(
        self,
        job_id: int,
        error_type: str,
        error_message: str,
    ) -> dict[str, Any]:
        return self.repository.update(
            job_id,
            {
                "job_status": "FAILED",
                "finished_at": utc_now_iso(),
                "error_type": error_type,
                "error_message": error_message,
            },
        )
