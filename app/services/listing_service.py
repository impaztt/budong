from __future__ import annotations

from typing import Any

from app.repositories.listing_repository import ListingRepository
from app.utils.date_utils import utc_now_iso


class ListingService:
    def __init__(self, repository: ListingRepository | None = None) -> None:
        self.repository = repository or ListingRepository()

    def save_listings(
        self,
        source: dict[str, Any],
        crawl_job_id: int,
        listings: list[dict[str, Any]],
    ) -> dict[str, int]:
        success_count = 0
        failed_count = 0
        seen_article_numbers: list[str] = []

        for listing in listings:
            article_no = listing.get("article_no")
            if not article_no:
                failed_count += 1
                continue

            source_type = listing.get("source_type") or source.get("source_type")
            now = utc_now_iso()
            payload = {
                **listing,
                "source_url_id": source.get("id"),
                "source_type": source_type,
                "source_url": listing.get("source_url") or source.get("resolved_url") or source.get("source_url"),
                "last_seen_at": now,
                "updated_at": now,
                "is_active": True,
            }
            saved = self.repository.upsert_listing(payload)
            self.repository.insert_snapshot(
                {
                    "listing_id": saved.get("id"),
                    "source_url_id": source.get("id"),
                    "crawl_job_id": crawl_job_id,
                    "source_type": source_type,
                    "article_no": article_no,
                    "snapshot_data": listing.get("raw_data") or listing,
                    "price_amount": payload.get("price_amount"),
                    "deposit_amount": payload.get("deposit_amount"),
                    "monthly_rent_amount": payload.get("monthly_rent_amount"),
                }
            )
            seen_article_numbers.append(article_no)
            success_count += 1

        return {
            "total_count": len(listings),
            "success_count": success_count,
            "failed_count": failed_count,
        }
