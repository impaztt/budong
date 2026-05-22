from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CrawlLog(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    crawl_job_id: int | None = None
    source_url_id: int | None = None
    request_url: str
    http_status: int | None = None
    success: bool = False
    error_type: str | None = None
    error_message: str | None = None
    requested_at: datetime | None = None
    elapsed_ms: int | None = None

    def to_db_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)
