from __future__ import annotations

from typing import Any

from app.repositories.supabase_client import get_supabase_client


class CrawlJobRepository:
    def __init__(self, client: Any | None = None) -> None:
        self.client = client or get_supabase_client()

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.client.table("crawl_jobs").insert(payload).execute()
        return result.data[0]

    def update(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.client.table("crawl_jobs").update(payload).eq("id", job_id).execute()
        return result.data[0]

    def get(self, job_id: int) -> dict[str, Any] | None:
        result = (
            self.client.table("crawl_jobs")
            .select("*")
            .eq("id", job_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
