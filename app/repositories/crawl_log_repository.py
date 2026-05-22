from __future__ import annotations

from typing import Any

from app.repositories.supabase_client import get_supabase_client


class CrawlLogRepository:
    def __init__(self, client: Any | None = None) -> None:
        self.client = client or get_supabase_client()

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.client.table("crawl_logs").insert(payload).execute()
        return result.data[0]

    def create_many(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not payloads:
            return []
        result = self.client.table("crawl_logs").insert(payloads).execute()
        return result.data or []
