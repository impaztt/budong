from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.exporters.excel_exporter import ExcelExporter
from app.repositories.listing_repository import ListingRepository
from app.utils.date_utils import timestamp_for_filename


class ExportService:
    def __init__(
        self,
        repository: ListingRepository | None = None,
        exporter: ExcelExporter | None = None,
    ) -> None:
        self.repository = repository or ListingRepository()
        self.exporter = exporter or ExcelExporter()

    def export(
        self,
        source_id: int | None = None,
        all_records: bool = False,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> Path:
        if not all_records and source_id is None and not (from_date or to_date):
            raise ValueError("Use --source-id, --all, or a date range.")

        records = self.repository.list_listings(
            source_id=source_id,
            from_date=from_date,
            to_date=to_date,
        )
        if not records:
            raise ValueError("NO_DATA_TO_EXPORT")

        output_path = self._build_output_path(source_id=source_id, all_records=all_records)
        self.exporter.export(records, output_path)
        return output_path

    def _build_output_path(self, source_id: int | None, all_records: bool) -> Path:
        settings.export_dir.mkdir(parents=True, exist_ok=True)
        stamp = timestamp_for_filename()
        if source_id is not None and not all_records:
            filename = f"real_estate_listings_source_{source_id}_{stamp}.xlsx"
        else:
            filename = f"real_estate_listings_all_{stamp}.xlsx"
        return settings.export_dir / filename
