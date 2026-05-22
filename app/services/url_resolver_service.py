from __future__ import annotations

from dataclasses import dataclass

import requests

from app.config.settings import settings
from app.utils.url_utils import detect_source_type, validate_http_url


@dataclass(frozen=True)
class ResolvedUrl:
    source_url: str
    resolved_url: str
    source_type: str


class UrlResolverService:
    def resolve(self, source_url: str) -> ResolvedUrl:
        validate_http_url(source_url)

        resolved_url = self._resolve_redirects(source_url)
        source_type = detect_source_type(resolved_url)
        if source_type == "UNKNOWN":
            source_type = detect_source_type(source_url)

        return ResolvedUrl(
            source_url=source_url,
            resolved_url=resolved_url,
            source_type=source_type,
        )

    def _resolve_redirects(self, source_url: str) -> str:
        try:
            response = requests.head(
                source_url,
                allow_redirects=True,
                timeout=settings.crawl_timeout_seconds,
            )
            if response.status_code < 400:
                return response.url
        except requests.RequestException:
            pass

        response = requests.get(
            source_url,
            allow_redirects=True,
            timeout=settings.crawl_timeout_seconds,
            stream=True,
        )
        response.close()
        if response.status_code in {403, 429}:
            raise ValueError(f"URL resolution stopped with HTTP {response.status_code}.")
        if response.status_code >= 400:
            raise ValueError(f"URL resolution failed with HTTP {response.status_code}.")
        return response.url
