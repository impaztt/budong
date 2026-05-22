from __future__ import annotations

from typing import Any

from app.repositories.supabase_client import get_supabase_client


class ListingRepository:
    def __init__(self, client: Any | None = None) -> None:
        self.client = client or get_supabase_client()

    def upsert_listing(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = (
            self.client.table("real_estate_listings")
            .upsert(payload, on_conflict="source_type,article_no")
            .execute()
        )
        return result.data[0]

    def insert_snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.client.table("real_estate_listing_snapshots").insert(payload).execute()
        return result.data[0]

    def list_listings(
        self,
        source_id: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[dict[str, Any]]:
        query = self.client.table("real_estate_listings").select("*").order("id")
        if source_id is not None:
            query = query.eq("source_url_id", source_id)
        if from_date:
            query = query.gte("last_seen_at", from_date)
        if to_date:
            query = query.lte("last_seen_at", to_date)
        result = query.execute()
        return result.data or []
