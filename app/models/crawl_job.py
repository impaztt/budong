from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CrawlJob(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    source_url_id: int
    job_status: str = "READY"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    error_type: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None

    def to_db_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)
