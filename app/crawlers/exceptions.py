from __future__ import annotations


class CrawlerError(RuntimeError):
    error_type = "CRAWLER_ERROR"


class CrawlRequestError(CrawlerError):
    error_type = "REQUEST_FAILED"


class RateLimitedCrawlError(CrawlerError):
    error_type = "HTTP_429_TOO_MANY_REQUESTS"


class BlockedCrawlError(CrawlerError):
    error_type = "HTTP_403_FORBIDDEN"


class UnsupportedCrawlerError(CrawlerError):
    error_type = "UNSUPPORTED_SOURCE"
