from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook


COLUMN_MAP = OrderedDict(
    [
        ("source_url_id", "URL ID"),
        ("article_no", "매물번호"),
        ("trade_type", "거래유형"),
        ("property_type", "매물유형"),
        ("complex_name", "단지명"),
        ("building_name", "동"),
        ("floor_info", "층"),
        ("direction", "방향"),
        ("area_m2", "공급면적"),
        ("exclusive_area_m2", "전용면적"),
        ("price_text", "가격 원문"),
        ("price_amount", "매매가"),
        ("deposit_amount", "보증금"),
        ("monthly_rent_amount", "월세"),
        ("realtor_name", "중개사"),
        ("confirmed_at", "확인일"),
        ("description", "설명"),
        ("source_url", "원본 URL"),
        ("first_seen_at", "최초 수집일"),
        ("last_seen_at", "최근 수집일"),
        ("is_active", "활성 여부"),
    ]
)


class ExcelExporter:
    def export(self, records: list[dict[str, Any]], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        normalized_records = [
            {column: record.get(column) for column in COLUMN_MAP.keys()}
            for record in records
        ]
        df = pd.DataFrame(normalized_records)
        df = df.rename(columns=COLUMN_MAP)
        df.to_excel(output_path, index=False)
        self._adjust_widths(output_path)
        return output_path

    def _adjust_widths(self, output_path: Path) -> None:
        workbook = load_workbook(output_path)
        worksheet = workbook.active
        for column_cells in worksheet.columns:
            width = max(
                len(str(cell.value)) if cell.value is not None else 0
                for cell in column_cells
            )
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(
                max(width + 2, 10),
                60,
            )
        workbook.save(output_path)
