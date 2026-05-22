from __future__ import annotations

import re


_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
_REMOVE_WORDS_RE = re.compile(
    r"(매매|전세|월세|보증금|가격|원|만원|만|억|보증|임대료|월)"
)


def _to_number(value: str) -> float | None:
    cleaned = value.replace(",", "").strip()
    match = _NUMBER_RE.search(cleaned)
    if not match:
        return None
    return float(match.group(0))


def _strip_labels(value: str) -> str:
    return (
        value.replace("매매", "")
        .replace("전세", "")
        .replace("월세", "")
        .replace("보증금", "")
        .replace("가격", "")
        .replace("원", "")
        .strip()
    )


def parse_korean_money(value: object, default_unit: int = 10_000) -> int | None:
    """Parse common Korean real-estate price text into KRW.

    Bare numbers are treated as 만원 units because real-estate listings commonly
    omit the unit in expressions such as 5000/120.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value * default_unit
    if isinstance(value, float):
        return int(value * default_unit)

    text = _strip_labels(str(value)).replace(",", "").strip()
    if not text or text in {"-", "협의"}:
        return None

    amount = 0.0
    remaining = text

    eok_match = re.search(r"(\d+(?:\.\d+)?)\s*억", remaining)
    if eok_match:
        amount += float(eok_match.group(1)) * 100_000_000
        remaining = remaining[eok_match.end() :]

    man_match = re.search(r"(\d+(?:\.\d+)?)\s*만", remaining)
    if man_match:
        amount += float(man_match.group(1)) * 10_000
        remaining = remaining[man_match.end() :]

    if eok_match and not man_match:
        rest_number = _to_number(_REMOVE_WORDS_RE.sub("", remaining))
        if rest_number:
            amount += rest_number * 10_000

    if amount:
        return int(amount)

    bare_number = _to_number(text)
    if bare_number is None:
        return None
    return int(bare_number * default_unit)


def parse_price_text(
    price_text: object,
    trade_type: object | None = None,
) -> dict[str, int | None]:
    text = "" if price_text is None else str(price_text).strip()
    trade = "" if trade_type is None else str(trade_type)
    result: dict[str, int | None] = {
        "price_amount": None,
        "deposit_amount": None,
        "monthly_rent_amount": None,
    }

    if not text:
        return result

    if "/" in text or "월세" in trade or "월세" in text:
        parts = text.replace("월세", "").split("/", maxsplit=1)
        result["deposit_amount"] = parse_korean_money(parts[0])
        if len(parts) > 1:
            result["monthly_rent_amount"] = parse_korean_money(parts[1])
        return result

    amount = parse_korean_money(text)
    if "전세" in trade or "전세" in text:
        result["deposit_amount"] = amount
    else:
        result["price_amount"] = amount
    return result
