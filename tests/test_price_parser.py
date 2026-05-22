from app.utils.price_parser import parse_korean_money, parse_price_text


def test_parse_sale_prices() -> None:
    assert parse_korean_money("6억 7,000") == 670_000_000
    assert parse_korean_money("12억") == 1_200_000_000
    assert parse_korean_money("9억 500") == 905_000_000


def test_parse_jeonse_price() -> None:
    parsed = parse_price_text("전세 4억 5,000", "전세")
    assert parsed["deposit_amount"] == 450_000_000
    assert parsed["price_amount"] is None


def test_parse_monthly_rent_price() -> None:
    parsed = parse_price_text("월세 1억/150", "월세")
    assert parsed["deposit_amount"] == 100_000_000
    assert parsed["monthly_rent_amount"] == 1_500_000

    parsed = parse_price_text("5000/120", "월세")
    assert parsed["deposit_amount"] == 50_000_000
    assert parsed["monthly_rent_amount"] == 1_200_000
