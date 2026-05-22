from __future__ import annotations

import re


_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)")


def parse_area_m2(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace(",", "").strip()
    match = _NUMBER_RE.search(text)
    if not match:
        return None
    return float(match.group(1))
