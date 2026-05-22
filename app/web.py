from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.config.settings import settings
from app.config.logging_config import configure_logging
from app.repositories.listing_repository import ListingRepository
from app.repositories.supabase_client import SupabaseConfigurationError
from app.services.crawl_orchestrator import CrawlOrchestrator
from app.services.local_preview_service import LocalPreviewService
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
            "local_sources": "/api/sources-local",
            "listings": "/api/listings",
            "local_listings": "/api/listings-local",
            "listings_by_source": "/api/listings?source_id=1",
            "crawl_source": "POST /api/crawl/source/1",
            "crawl_url": "POST /api/crawl-url",
            "local_crawl_url": "POST /api/crawl-url-local",
        },
        "view": "/view",
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
        if settings.has_supabase_credentials:
            rows = SourceUrlService().list_source_urls(
                active_only=active_only,
                status=status,
            )
            storage = "supabase"
        else:
            rows = LocalPreviewService().list_sources()
            if active_only:
                rows = [row for row in rows if row.get("active_yn") == "Y"]
            if status:
                rows = [row for row in rows if row.get("crawl_status") == status]
            storage = "local"
        return _json({"storage": storage, "count": len(rows), "data": rows})
    except Exception as exc:
        _raise_api_error(exc)


@app.get("/api/sources-local")
def list_sources_local() -> dict[str, Any]:
    try:
        rows = LocalPreviewService().list_sources()
        return _json({"storage": "local", "count": len(rows), "data": rows})
    except Exception as exc:
        _raise_api_error(exc)


@app.get("/api/listings-local")
def list_listings_local(
    source_id: int | None = Query(None, description="Filter by local source id"),
) -> dict[str, Any]:
    try:
        rows = LocalPreviewService().list_listings(source_id=source_id)
        return _json({"storage": "local", "count": len(rows), "data": rows})
    except Exception as exc:
        _raise_api_error(exc)


@app.post("/api/crawl-url-local")
def crawl_url_local(request: CrawlUrlRequest) -> dict[str, Any]:
    try:
        result = LocalPreviewService().crawl_url(request.url, memo=request.memo)
        return _json({"storage": "local", "data": result})
    except Exception as exc:
        _raise_api_error(exc)


@app.get("/view", response_class=HTMLResponse)
def preview_view() -> str:
    return """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Real Estate Listing Collector Preview</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; color: #172033; background: #f6f7f9; }
    main { max-width: 1120px; margin: 0 auto; padding: 28px 20px; }
    h1 { font-size: 24px; margin: 0 0 16px; }
    form { display: grid; grid-template-columns: 1fr auto; gap: 8px; margin-bottom: 16px; }
    input { padding: 10px 12px; border: 1px solid #c9ced6; border-radius: 6px; font-size: 14px; }
    button { padding: 10px 14px; border: 0; border-radius: 6px; background: #1769e0; color: white; font-weight: 700; cursor: pointer; }
    button:disabled { opacity: .55; cursor: wait; }
    .bar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
    .status { color: #596274; font-size: 13px; }
    pre { min-height: 520px; overflow: auto; margin: 0; padding: 16px; border: 1px solid #d9dde5; border-radius: 8px; background: white; font-size: 13px; line-height: 1.45; white-space: pre-wrap; word-break: break-word; }
    @media (max-width: 720px) {
      form { grid-template-columns: 1fr; }
      main { padding: 18px 12px; }
    }
  </style>
</head>
<body>
  <main>
    <h1>부동산 매물 로컬 JSON 미리보기</h1>
    <form id="crawl-form">
      <input id="url" type="url" value="https://naver.me/FtoGnVDq" placeholder="수집할 URL" required>
      <button id="crawl-button" type="submit">크롤링 실행</button>
    </form>
    <div class="bar">
      <button id="reload-button" type="button">저장된 JSON 새로고침</button>
      <span id="status" class="status">로컬 파일 저장소를 사용합니다. Supabase에는 저장하지 않습니다.</span>
    </div>
    <pre id="output">Loading...</pre>
  </main>
  <script>
    const output = document.getElementById("output");
    const statusEl = document.getElementById("status");
    const crawlButton = document.getElementById("crawl-button");

    function show(data) {
      output.textContent = JSON.stringify(data, null, 2);
    }

    async function loadListings() {
      statusEl.textContent = "저장된 로컬 JSON을 불러오는 중...";
      const response = await fetch("/api/listings-local");
      const data = await response.json();
      show(data);
      statusEl.textContent = `로컬 저장 매물 ${data.count ?? 0}건`;
    }

    document.getElementById("reload-button").addEventListener("click", loadListings);

    document.getElementById("crawl-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const url = document.getElementById("url").value;
      crawlButton.disabled = true;
      statusEl.textContent = "크롤링 중... robots.txt 확인과 보수적 요청 지연을 적용합니다.";
      try {
        const response = await fetch("/api/crawl-url-local", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url })
        });
        const data = await response.json();
        show(data);
        statusEl.textContent = response.ok
          ? `수집 완료: ${data.data?.total_count ?? 0}건`
          : "수집 실패";
      } catch (error) {
        show({ error: String(error) });
        statusEl.textContent = "요청 실패";
      } finally {
        crawlButton.disabled = false;
      }
    });

    loadListings();
  </script>
</body>
</html>
"""


@app.get("/api/sources/{source_id}")
def get_source(source_id: int) -> dict[str, Any]:
    try:
        if settings.has_supabase_credentials:
            row = SourceUrlService().get_source_url(source_id)
            storage = "supabase"
        else:
            rows = LocalPreviewService().list_sources()
            row = next((item for item in rows if item.get("id") == source_id), None)
            if row is None:
                raise ValueError(f"Local source not found: {source_id}")
            storage = "local"
        return _json({"storage": storage, "data": row})
    except Exception as exc:
        _raise_api_error(exc)


@app.get("/api/listings")
def list_listings(
    source_id: int | None = Query(None, description="Filter by source_urls.id"),
    from_date: str | None = Query(None, description="Filter last_seen_at from YYYY-MM-DD"),
    to_date: str | None = Query(None, description="Filter last_seen_at to YYYY-MM-DD"),
) -> dict[str, Any]:
    try:
        if settings.has_supabase_credentials:
            rows = ListingRepository().list_listings(
                source_id=source_id,
                from_date=from_date,
                to_date=to_date,
            )
            storage = "supabase"
        else:
            rows = LocalPreviewService().list_listings(source_id=source_id)
            storage = "local"
        return _json({"storage": storage, "count": len(rows), "data": rows})
    except Exception as exc:
        _raise_api_error(exc)


@app.post("/api/crawl/source/{source_id}")
def crawl_source(source_id: int) -> dict[str, Any]:
    try:
        if not settings.has_supabase_credentials:
            raise ValueError("Source-id crawl requires Supabase. Use /api/crawl-url-local for local preview.")
        result = CrawlOrchestrator().crawl_source(source_id)
        return _json({"storage": "supabase", "data": result})
    except Exception as exc:
        _raise_api_error(exc)


@app.post("/api/crawl-url")
def crawl_url(request: CrawlUrlRequest) -> dict[str, Any]:
    try:
        if settings.has_supabase_credentials:
            result = CrawlOrchestrator().crawl_url(request.url, memo=request.memo)
            storage = "supabase"
        else:
            result = LocalPreviewService().crawl_url(request.url, memo=request.memo)
            storage = "local"
        return _json({"storage": storage, "data": result})
    except Exception as exc:
        _raise_api_error(exc)
