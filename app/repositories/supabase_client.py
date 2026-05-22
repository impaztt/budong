from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.config.settings import settings


class SupabaseConfigurationError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_supabase_client() -> Any:
    if not settings.has_supabase_credentials:
        raise SupabaseConfigurationError(
            "SUPABASE_URL and SUPABASE_KEY must be set in .env before using DB commands."
        )

    try:
        from supabase import create_client
    except ImportError as exc:
        raise SupabaseConfigurationError(
            "supabase package is not installed. Run pip install -r requirements.txt."
        ) from exc

    return create_client(settings.supabase_url, settings.supabase_key)
