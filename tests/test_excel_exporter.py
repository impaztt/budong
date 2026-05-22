from openpyxl import load_workbook

from app.exporters.excel_exporter import ExcelExporter


def test_export_excel(tmp_path) -> None:
    output_path = tmp_path / "listings.xlsx"
    records = [
        {
            "source_url_id": 1,
            "article_no": "123",
            "trade_type": "매매",
            "property_type": "아파트",
            "complex_name": "테스트단지",
            "price_amount": 670_000_000,
            "is_active": True,
        }
    ]

    ExcelExporter().export(records, output_path)

    workbook = load_workbook(output_path)
    sheet = workbook.active
    assert sheet["A1"].value == "URL ID"
    assert sheet["B1"].value == "매물번호"
    assert sheet["B2"].value == "123"
