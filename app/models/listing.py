from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class Listing(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    source_url_id: int | None = None
    source_type: str
    article_no: str
    trade_type: str | None = None
    property_type: str | None = None
    complex_name: str | None = None
    building_name: str | None = None
    room_info: str | None = None
    floor_info: str | None = None
    direction: str | None = None
    area_m2: float | None = None
    exclusive_area_m2: float | None = None
    price_text: str | None = None
    price_amount: int | None = None
    deposit_amount: int | None = None
    monthly_rent_amount: int | None = None
    realtor_name: str | None = None
    confirmed_at: str | None = None
    description: str | None = None
    source_url: str | None = None
    raw_data: dict[str, Any] | list[Any] | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool = True

    def to_db_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)
