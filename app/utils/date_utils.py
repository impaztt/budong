from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp_for_filename(now: datetime | None = None) -> str:
    target = now or datetime.now()
    return target.strftime("%Y%m%d_%H%M%S")
