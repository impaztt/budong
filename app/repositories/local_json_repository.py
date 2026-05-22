from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any

from app.config.settings import settings


class LocalJsonRepository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.local_data_dir / "preview_store.json"
        self._lock = Lock()

    def list_sources(self) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(self._load()["sources"])

    def list_listings(
        self,
        source_id: int | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            listings = self._load()["listings"]
            if source_id is not None:
                listings = [
                    row for row in listings if row.get("source_url_id") == source_id
                ]
            return deepcopy(listings)

    def upsert_source(
        self,
        source_url: str,
        resolved_url: str,
        source_type: str,
        memo: str | None,
        status: str,
    ) -> dict[str, Any]:
        with self._lock:
            store = self._load()
            source = self._find_source(store, source_url, resolved_url)
            if source is None:
                next_id = self._next_id(store["sources"])
                source = {
                    "id": next_id,
                    "source_url": source_url,
                    "resolved_url": resolved_url,
                    "source_type": source_type,
                    "memo": memo,
                    "active_yn": "Y",
                    "crawl_status": status,
                    "last_crawled_at": None,
                    "last_success_at": None,
                    "last_failed_at": None,
                    "last_error_message": None,
                    "last_count": 0,
                }
                store["sources"].append(source)
            else:
                source.update(
                    {
                        "resolved_url": resolved_url,
                        "source_type": source_type,
                        "memo": memo if memo is not None else source.get("memo"),
                        "crawl_status": status,
                    }
                )
            self._save(store)
            return deepcopy(source)

    def update_source(self, source_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            store = self._load()
            for source in store["sources"]:
                if source["id"] == source_id:
                    source.update(payload)
                    self._save(store)
                    return deepcopy(source)
            raise ValueError(f"Local source not found: {source_id}")

    def upsert_listings(
        self,
        source_id: int,
        listings: list[dict[str, Any]],
    ) -> None:
        with self._lock:
            store = self._load()
            remaining = [
                row for row in store["listings"] if row.get("source_url_id") != source_id
            ]
            remaining.extend(listings)
            store["listings"] = remaining
            self._save(store)

    def append_logs(
        self,
        source_id: int,
        logs: list[dict[str, Any]],
    ) -> None:
        with self._lock:
            store = self._load()
            store["crawl_logs"].extend(
                {**log, "source_url_id": source_id} for log in logs
            )
            self._save(store)

    def _find_source(
        self,
        store: dict[str, Any],
        source_url: str,
        resolved_url: str,
    ) -> dict[str, Any] | None:
        for source in store["sources"]:
            if source.get("source_url") == source_url:
                return source
            if resolved_url and source.get("resolved_url") == resolved_url:
                return source
        return None

    def _next_id(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 1
        return max(int(row["id"]) for row in rows) + 1

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"sources": [], "listings": [], "crawl_logs": []}
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _save(self, store: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(store, file, ensure_ascii=False, indent=2)
