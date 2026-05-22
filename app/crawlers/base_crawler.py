from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from loguru import logger

from app.config.settings import settings
from app.crawlers.exceptions import (
    BlockedCrawlError,
    CrawlRequestError,
    RateLimitedCrawlError,
)
from app.utils.delay import sleep_seconds


@dataclass
class CrawlResult:
    source_url_id: int | None
    source_type: str
    listings: list[dict[str, Any]]
    request_logs: list[dict[str, Any]] = field(default_factory=list)
    raw_length: int = 0
    raw_preview: str | None = None
    parser_message: str | None = None


class BaseCrawler:
    def __init__(self) -> None:
        self.session = requests.Session()
        self._last_request_at = 0.0
        self.request_logs: list[dict[str, Any]] = []
        self._robots_cache: dict[str, RobotFileParser | None] = {}

    def crawl(self, source: dict[str, Any]) -> CrawlResult:
        raise NotImplementedError

    def fetch(self, url: str) -> requests.Response:
        self._ensure_robots_allowed(url)
        last_error: Exception | None = None
        max_attempts = settings.crawl_max_retry + 1

        for attempt in range(1, max_attempts + 1):
            self._wait_before_request()
            requested_at = datetime.now(timezone.utc)
            started = time.perf_counter()
            try:
                response = self.session.get(
                    url,
                    timeout=settings.crawl_timeout_seconds,
                    allow_redirects=True,
                )
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                self._record_log(
                    request_url=url,
                    http_status=response.status_code,
                    success=200 <= response.status_code < 300,
                    requested_at=requested_at,
                    elapsed_ms=elapsed_ms,
                )

                if response.status_code == 429:
                    raise RateLimitedCrawlError("HTTP 429 rate limited; crawling stopped.")
                if response.status_code == 403:
                    raise BlockedCrawlError("HTTP 403 forbidden; crawling stopped.")
                if 400 <= response.status_code < 500:
                    raise CrawlRequestError(f"HTTP {response.status_code} client error.")
                if response.status_code >= 500:
                    if attempt < max_attempts:
                        continue
                    raise CrawlRequestError(f"HTTP {response.status_code} server error.")

                response.raise_for_status()
                return response
            except requests.Timeout as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                last_error = exc
                self._record_log(
                    request_url=url,
                    http_status=None,
                    success=False,
                    error_type="REQUEST_TIMEOUT",
                    error_message=str(exc),
                    requested_at=requested_at,
                    elapsed_ms=elapsed_ms,
                )
                if attempt < max_attempts:
                    continue
            except (BlockedCrawlError, RateLimitedCrawlError):
                raise
            except requests.RequestException as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                last_error = exc
                self._record_log(
                    request_url=url,
                    http_status=getattr(exc.response, "status_code", None),
                    success=False,
                    error_type="REQUEST_FAILED",
                    error_message=str(exc),
                    requested_at=requested_at,
                    elapsed_ms=elapsed_ms,
                )
                if attempt < max_attempts:
                    continue

        raise CrawlRequestError(str(last_error) if last_error else "Request failed.")

    def _ensure_robots_allowed(self, url: str) -> None:
        robots_url = self._robots_url_for(url)
        if robots_url not in self._robots_cache:
            self._robots_cache[robots_url] = self._load_robots(robots_url)

        parser = self._robots_cache[robots_url]
        if parser is not None and not parser.can_fetch("*", url):
            raise CrawlRequestError(f"robots.txt disallows fetching URL: {url}")

    def _load_robots(self, robots_url: str) -> RobotFileParser | None:
        self._wait_before_request()
        requested_at = datetime.now(timezone.utc)
        started = time.perf_counter()
        try:
            response = self.session.get(
                robots_url,
                timeout=settings.crawl_timeout_seconds,
                allow_redirects=True,
            )
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            self._record_log(
                request_url=robots_url,
                http_status=response.status_code,
                success=200 <= response.status_code < 300,
                requested_at=requested_at,
                elapsed_ms=elapsed_ms,
            )

            if response.status_code == 429:
                raise RateLimitedCrawlError("HTTP 429 while checking robots.txt.")
            if response.status_code == 403:
                raise BlockedCrawlError("HTTP 403 while checking robots.txt.")
            if response.status_code == 404:
                return None
            if response.status_code >= 500:
                raise CrawlRequestError(
                    f"robots.txt check failed with HTTP {response.status_code}."
                )
            if response.status_code >= 400:
                raise CrawlRequestError(
                    f"robots.txt check failed with HTTP {response.status_code}."
                )

            parser = RobotFileParser()
            parser.set_url(response.url)
            parser.parse(response.text.splitlines())
            return parser
        except requests.Timeout as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            self._record_log(
                request_url=robots_url,
                http_status=None,
                success=False,
                error_type="REQUEST_TIMEOUT",
                error_message=str(exc),
                requested_at=requested_at,
                elapsed_ms=elapsed_ms,
            )
            raise CrawlRequestError("robots.txt check timed out.") from exc
        except requests.RequestException as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            self._record_log(
                request_url=robots_url,
                http_status=getattr(exc.response, "status_code", None),
                success=False,
                error_type="REQUEST_FAILED",
                error_message=str(exc),
                requested_at=requested_at,
                elapsed_ms=elapsed_ms,
            )
            raise CrawlRequestError("robots.txt check failed.") from exc

    def _robots_url_for(self, url: str) -> str:
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))

    def _wait_before_request(self) -> None:
        elapsed = time.perf_counter() - self._last_request_at
        wait_for = settings.crawl_delay_seconds - elapsed
        if wait_for > 0:
            sleep_seconds(wait_for)
        self._last_request_at = time.perf_counter()

    def _record_log(
        self,
        request_url: str,
        http_status: int | None,
        success: bool,
        requested_at: datetime,
        elapsed_ms: int,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        log_entry = {
            "request_url": request_url,
            "http_status": http_status,
            "success": success,
            "error_type": error_type,
            "error_message": error_message,
            "requested_at": requested_at.isoformat(),
            "elapsed_ms": elapsed_ms,
        }
        self.request_logs.append(log_entry)
        logger.bind(category="crawl").info(
            "request url={} status={} success={} elapsed_ms={}",
            request_url,
            http_status,
            success,
            elapsed_ms,
        )
