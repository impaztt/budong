from __future__ import annotations

import re


_SPACE_RE = re.compile(r"\s+")


def clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return _SPACE_RE.sub(" ", text)
