from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from bs4 import BeautifulSoup

from app.parsers.base_parser import BaseParser
from app.utils.area_parser import parse_area_m2
from app.utils.price_parser import parse_price_text
from app.utils.text_cleaner import clean_text


class NaverLandParser(BaseParser):
    ARTICLE_NO_KEYS = ("articleNo", "article_no", "atclNo", "atcl_no")

    def parse(self, raw_content: str, source_url: str | None = None) -> list[dict]:
        payloads = self._extract_payloads(raw_content)
        listings: list[dict] = []
        seen: set[str] = set()

        for payload in payloads:
            for item in self._walk_article_dicts(payload):
                listing = self._normalize_article(item, source_url)
                article_no = listing.get("article_no")
                if not article_no or article_no in seen:
                    continue
                seen.add(article_no)
                listings.append(listing)

        return listings

    def _extract_payloads(self, raw_content: str) -> list[Any]:
        payloads: list[Any] = []

        try:
            payloads.append(json.loads(raw_content))
            return payloads
        except json.JSONDecodeError:
            pass

        soup = BeautifulSoup(raw_content, "html.parser")
        for script in soup.find_all("script"):
            text = script.string or script.get_text(strip=True)
            if not text:
                continue
            candidate = text.strip()
            if not (candidate.startswith("{") or candidate.startswith("[")):
                continue
            try:
                payloads.append(json.loads(candidate))
            except json.JSONDecodeError:
                continue

        return payloads

    def _walk_article_dicts(self, payload: Any) -> Iterable[dict[str, Any]]:
        if isinstance(payload, dict):
            if self._has_article_no(payload):
                yield payload
            for value in payload.values():
                yield from self._walk_article_dicts(value)
        elif isinstance(payload, list):
            for item in payload:
                yield from self._walk_article_dicts(item)

    def _has_article_no(self, value: dict[str, Any]) -> bool:
        return any(value.get(key) for key in self.ARTICLE_NO_KEYS)

    def _pick(self, item: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = item.get(key)
            if value not in (None, ""):
                return value
        return None

    def _normalize_article(
        self,
        item: dict[str, Any],
        source_url: str | None,
    ) -> dict[str, Any]:
        article_no = clean_text(self._pick(item, *self.ARTICLE_NO_KEYS))
        trade_type = clean_text(
            self._pick(item, "tradeTypeName", "tradeType", "trade_type", "tradTpNm")
        )
        price_text = clean_text(
            self._pick(
                item,
                "dealOrWarrantPrc",
                "priceText",
                "price_text",
                "rentPrc",
                "prc",
            )
        )
        parsed_price = parse_price_text(price_text, trade_type)

        description = self._pick(
            item,
            "articleFeatureDesc",
            "articleDesc",
            "description",
            "atclFetrDesc",
        )
        if isinstance(description, list):
            description = ", ".join(str(part) for part in description if part)

        return {
            "source_type": "NAVER_LAND",
            "article_no": article_no,
            "trade_type": trade_type,
            "property_type": clean_text(
                self._pick(
                    item,
                    "realEstateTypeName",
                    "realEstateType",
                    "property_type",
                    "rletTpNm",
                )
            ),
            "complex_name": clean_text(
                self._pick(item, "complexName", "complex_name", "hscpNm")
            ),
            "building_name": clean_text(
                self._pick(item, "buildingName", "building_name", "dongName")
            ),
            "room_info": clean_text(self._pick(item, "roomInfo", "room_info")),
            "floor_info": clean_text(self._pick(item, "floorInfo", "floor_info", "flrInfo")),
            "direction": clean_text(self._pick(item, "direction", "directionName", "directionNm")),
            "area_m2": parse_area_m2(
                self._pick(item, "area1", "supplyArea", "area_m2", "spc1")
            ),
            "exclusive_area_m2": parse_area_m2(
                self._pick(
                    item,
                    "area2",
                    "exclusiveArea",
                    "exclusive_area_m2",
                    "spc2",
                )
            ),
            "price_text": price_text,
            "price_amount": parsed_price["price_amount"],
            "deposit_amount": parsed_price["deposit_amount"],
            "monthly_rent_amount": parsed_price["monthly_rent_amount"],
            "realtor_name": clean_text(
                self._pick(item, "realtorName", "realtor_name", "cpName", "rltrNm")
            ),
            "confirmed_at": clean_text(
                self._pick(item, "articleConfirmYmd", "confirmYmd", "confirmed_at")
            ),
            "description": clean_text(description),
            "source_url": source_url,
            "raw_data": item,
        }
