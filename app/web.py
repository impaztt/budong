from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.config.logging_config import configure_logging
from app.repositories.listing_repository import ListingRepository
from app.repositories.supabase_client import SupabaseConfigurationError
from app.services.crawl_orchestrator import CrawlOrchestrator
from app.services.source_url_service import SourceUrlService


configure_logging()

app = FastAPI(
    title="Real Estate Listing Collector",
    version="0.1.0",
    description="Local JSON API for source URLs, crawled listings, and crawl execution.",
)


class CrawlUrlRequest(BaseModel):
    url: str
    memo: str | None = None


def _json(payload: Any) -> Any:
    return jsonable_encoder(payload)


def _raise_api_error(exc: Exception) -> None:
    if isinstance(exc, SupabaseConfigurationError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "Real Estate Listing Collector",
        "docs": "/docs",
        "json_endpoints": {
            "sources": "/api/sources",
            "listings": "/api/listings",
            "listings_by_source": "/api/listings?source_id=1",
            "crawl_source": "POST /api/crawl/source/1",
            "crawl_url": "POST /api/crawl-url",
        },
    }


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/sources")
def list_sources(
    active_only: bool = Query(False, description="Only active source URLs"),
    status: str | None = Query(None, description="Filter by crawl_status"),
) -> dict[str, Any]:
    try:
        rows = SourceUrlService().list_source_urls(
            active_only=active_only,
            status=status,
        )
        return _json({"count": len(rows), "data": rows})
    except Exception as exc:
        _raise_api_error(exc)


@app.get("/api/sources/{source_id}")
def get_source(source_id: int) -> dict[str, Any]:
    try:
        row = SourceUrlService().get_source_url(source_id)
        return _json({"data": row})
    except Exception as exc:
        _raise_api_error(exc)


@app.get("/api/listings")
def list_listings(
    source_id: int | None = Query(None, description="Filter by source_urls.id"),
    from_date: str | None = Query(None, description="Filter last_seen_at from YYYY-MM-DD"),
    to_date: str | None = Query(None, description="Filter last_seen_at to YYYY-MM-DD"),
) -> dict[str, Any]:
    try:
        rows = ListingRepository().list_listings(
            source_id=source_id,
            from_date=from_date,
            to_date=to_date,
        )
        return _json({"count": len(rows), "data": rows})
    except Exception as exc:
        _raise_api_error(exc)


@app.post("/api/crawl/source/{source_id}")
def crawl_source(source_id: int) -> dict[str, Any]:
    try:
        result = CrawlOrchestrator().crawl_source(source_id)
        return _json({"data": result})
    except Exception as exc:
        _raise_api_error(exc)


@app.post("/api/crawl-url")
def crawl_url(request: CrawlUrlRequest) -> dict[str, Any]:
    try:
        result = CrawlOrchestrator().crawl_url(request.url, memo=request.memo)
        return _json({"data": result})
    except Exception as exc:
        _raise_api_error(exc)
