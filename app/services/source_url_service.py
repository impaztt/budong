from __future__ import annotations

from typing import Any

from app.repositories.source_url_repository import SourceUrlRepository
from app.services.url_resolver_service import UrlResolverService
from app.utils.date_utils import utc_now_iso


class SourceUrlService:
    def __init__(
        self,
        repository: SourceUrlRepository | None = None,
        resolver: UrlResolverService | None = None,
    ) -> None:
        self.repository = repository or SourceUrlRepository()
        self.resolver = resolver or UrlResolverService()

    def register_url(self, source_url: str, memo: str | None = None) -> dict[str, Any]:
        resolved = self.resolver.resolve(source_url)
        existing = self.repository.find_by_source_or_resolved(
            source_url=resolved.source_url,
            resolved_url=resolved.resolved_url,
        )
        if existing:
            return existing

        return self.repository.create(
            {
                "source_url": resolved.source_url,
                "resolved_url": resolved.resolved_url,
                "source_type": resolved.source_type,
                "crawl_status": "PENDING",
                "active_yn": "Y",
                "memo": memo,
            }
        )

    def get_source_url(self, source_id: int) -> dict[str, Any]:
        source = self.repository.get(source_id)
        if not source:
            raise ValueError(f"source_url not found: {source_id}")
        return source

    def list_source_urls(
        self,
        active_only: bool = False,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.repository.list(active_only=active_only, status=status)

    def mark_active(self, source_id: int) -> dict[str, Any]:
        return self.repository.update(source_id, {"active_yn": "Y"})

    def mark_inactive(self, source_id: int) -> dict[str, Any]:
        return self.repository.update(source_id, {"active_yn": "N"})

    def update_crawl_status(
        self,
        source_id: int,
        status: str,
        error_message: str | None = None,
        success: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"crawl_status": status}
        now = utc_now_iso()
        payload["last_crawled_at"] = now
        if success:
            payload["last_success_at"] = now
        if error_message:
            payload["last_failed_at"] = now
            payload["last_error_message"] = error_message
        return self.repository.update(source_id, payload)
