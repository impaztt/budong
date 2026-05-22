from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceUrl(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    source_url: str
    resolved_url: str | None = None
    source_type: str = "UNKNOWN"
    crawl_status: str = "PENDING"
    active_yn: str = Field(default="Y", pattern="^[YN]$")
    memo: str | None = None
    last_crawled_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failed_at: datetime | None = None
    last_error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_db_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)
