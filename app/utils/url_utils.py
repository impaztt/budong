from __future__ import annotations

from urllib.parse import urlparse


NAVER_LAND_HOSTS = {
    "land.naver.com",
    "m.land.naver.com",
    "new.land.naver.com",
    "fin.land.naver.com",
}


def validate_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")


def get_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def detect_source_type(url: str) -> str:
    domain = get_domain(url)
    if domain in NAVER_LAND_HOSTS or domain.endswith(".land.naver.com"):
        return "NAVER_LAND"
    return "UNKNOWN"
