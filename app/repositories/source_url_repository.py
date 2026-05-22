from __future__ import annotations

from typing import Any

from app.repositories.supabase_client import get_supabase_client


class SourceUrlRepository:
    def __init__(self, client: Any | None = None) -> None:
        self.client = client or get_supabase_client()

    def find_by_source_or_resolved(
        self,
        source_url: str,
        resolved_url: str | None = None,
    ) -> dict[str, Any] | None:
        source_result = (
            self.client.table("source_urls")
            .select("*")
            .eq("source_url", source_url)
            .limit(1)
            .execute()
        )
        if source_result.data:
            return source_result.data[0]

        if not resolved_url:
            return None

        resolved_result = (
            self.client.table("source_urls")
            .select("*")
            .eq("resolved_url", resolved_url)
            .limit(1)
            .execute()
        )
        if resolved_result.data:
            return resolved_result.data[0]
        return None

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.client.table("source_urls").insert(payload).execute()
        return result.data[0]

    def get(self, source_id: int) -> dict[str, Any] | None:
        result = (
            self.client.table("source_urls")
            .select("*")
            .eq("id", source_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def list(
        self,
        active_only: bool = False,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query = self.client.table("source_urls").select("*").order("id")
        if active_only:
            query = query.eq("active_yn", "Y")
        if status:
            query = query.eq("crawl_status", status)
        result = query.execute()
        return result.data or []

    def update(self, source_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        result = (
            self.client.table("source_urls")
            .update(payload)
            .eq("id", source_id)
            .execute()
        )
        return result.data[0]
